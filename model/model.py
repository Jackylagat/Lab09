from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO
from model.escursione import Escursione


class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        self._escursioni_parco = []
        self._max_giorni = None
        self._max_budget = None

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        relazioni = EscursioneDAO.get_escursioni_punti_interesse()
        if relazioni is None:
            return
        for r in relazioni:
            escursione = self.escursioni_map[r["id_escursione"]]
            punto = self.punti_interesse_map[r["id_punto_interesse"]]
            escursione.punti_interesse.add(punto) # nel file escursione.py ogni oggetto Escursione ha un set di punti d'interesse
            punto.escursioni.add(escursione)      # nel file punto_interesse.py ogni oggetto PuntoInteresse ha un set di escursioni


    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        self._escursioni_parco = [e for e in self.escursioni_map.values() if e.id_parco == id_parco]
        self._max_giorni = max_giorni
        self._max_budget = max_budget

        self._ricorsione(0, [], 0, 0.0, 0, set())

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        # Si fa il controllo sui valori ottimi trovati finora
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()
            self._costo = costo_corrente

        for i in range(start_index, len(self._escursioni_parco)):
            escursione = self._escursioni_parco[i]

            # Vincoli
            if self._max_giorni is not None and durata_corrente + escursione.durata_giorni > self._max_giorni:
                continue # Se si sforano i giorni massimi, si salta questa escursione e si passa a quella dopo

            if self._max_budget is not None and costo_corrente + escursione.costo> self._max_budget:
                continue # Se si sfora il budget massimo, si salta questa escursione e si passa a quella dopo

            if len(escursione.punti_interesse.intersection(punti_usati)) > 0:
                continue # Se l'intersezione degli insiemi 'punti usati' e 'escursione.punti_interesse'
                         # non e' vuota vuol dire che quel puntio d'interesse e' gia' stato usato,
                         # quindi si passa alla escursione successiva

            # Calcolo parziale
            voto_escursione = sum(p.voto_visitatori for p in escursione.punti_interesse) # Dal file punto_interesse.py ogni oggetto p di questa classe
                                                                                         # che si trova nel set di ogni oggetto escursione, ha un attributo 'voto_visitatori'
            pacchetto_parziale.append(escursione)
            punti_usati.update(escursione.punti_interesse)

            # Ricorsione (i + 1 perche ogni escursione si usa al massimo 1 volta per pacchetto)
            self._ricorsione(i + 1,
                             pacchetto_parziale,
                             durata_corrente + escursione.durata_giorni,
                             costo_corrente + escursione.costo,
                             valore_corrente + voto_escursione,
                             punti_usati)


            # Backtracking
            pacchetto_parziale.pop()
            punti_usati.difference_update(escursione.punti_interesse)






