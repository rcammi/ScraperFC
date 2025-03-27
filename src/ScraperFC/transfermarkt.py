from .scraperfc_exceptions import InvalidLeagueException, InvalidYearException
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import pandas as pd
import cloudscraper
from typing import Sequence
import warnings

TRANSFERMARKT_ROOT = "https://www.transfermarkt.us"

comps = {
    "EPL": "https://www.transfermarkt.us/premier-league/startseite/wettbewerb/GB1",
    "EFL Championship": "https://www.transfermarkt.us/championship/startseite/wettbewerb/GB2",
    "EFL1": "https://www.transfermarkt.us/league-one/startseite/wettbewerb/GB3",
    "EFL2": "https://www.transfermarkt.us/league-two/startseite/wettbewerb/GB4",
    "Bundesliga": "https://www.transfermarkt.us/bundesliga/startseite/wettbewerb/L1",
    "2.Bundesliga": "https://www.transfermarkt.us/2-bundesliga/startseite/wettbewerb/L2",
    "Serie A": "https://www.transfermarkt.us/serie-a/startseite/wettbewerb/IT1",
    "Serie B": "https://www.transfermarkt.us/serie-b/startseite/wettbewerb/IT2",
    "La Liga": "https://www.transfermarkt.us/laliga/startseite/wettbewerb/ES1",
    "La Liga 2": "https://www.transfermarkt.us/laliga2/startseite/wettbewerb/ES2",
    "Ligue 1": "https://www.transfermarkt.us/ligue-1/startseite/wettbewerb/FR1",
    "Ligue 2": "https://www.transfermarkt.us/ligue-2/startseite/wettbewerb/FR2",
    "Eredivisie": "https://www.transfermarkt.us/eredivisie/startseite/wettbewerb/NL1",
    "Scottish PL": "https://www.transfermarkt.us/scottish-premiership/startseite/wettbewerb/SC1",
    "Super Lig": "https://www.transfermarkt.us/super-lig/startseite/wettbewerb/TR1",
    "Jupiler Pro League": "https://www.transfermarkt.us/jupiler-pro-league/startseite/wettbewerb/BE1",  # noqa: E501
    "Liga Nos": "https://www.transfermarkt.us/liga-nos/startseite/wettbewerb/PO1",
    "Russian Premier League": "https://www.transfermarkt.us/premier-liga/startseite/wettbewerb/RU1",
    "Brasileirao": "https://www.transfermarkt.us/campeonato-brasileiro-serie-a/startseite/wettbewerb/BRA1",  # noqa: E501
    "Argentina Liga Profesional": "https://www.transfermarkt.us/superliga/startseite/wettbewerb/AR1N",  # noqa: E501
    "MLS": "https://www.transfermarkt.us/major-league-soccer/startseite/wettbewerb/MLS1",
    "Turkish Super Lig": "https://www.transfermarkt.us/super-lig/startseite/wettbewerb/TR1",
    "Primavera 1": "https://www.transfermarkt.us/primavera-1/startseite/wettbewerb/IJ1",
    "Primavera 2 - A": "https://www.transfermarkt.us/primavera-2a/startseite/wettbewerb/IJ2A",
    "Primavera 2 - B": "https://www.transfermarkt.us/primavera-2b/startseite/wettbewerb/IJ2B",
    "Campionato U18": "https://www.transfermarkt.us/campionato-nazionale-under-18/startseite/wettbewerb/ITJ7",  # noqa: E501
    "Argentina Torneo Apertura": "https://www.transfermarkt.us/torneo-apertura/startseite/wettbewerb/ARG1", 
    "Colombia Liga Apertura": "https://www.transfermarkt.us/liga-dimayor-apertura/startseite/wettbewerb/COLP",
    "Chile Liga de Primera": "https://www.transfermarkt.us/liga-de-primera/startseite/wettbewerb/CLPD",
    "Ecuador Liga Pro Serie A": "https://www.transfermarkt.us/ligapro-serie-a/startseite/wettbewerb/EC1N",
    "Uruguay Liga Apertura": "https://www.transfermarkt.us/liga-auf-apertura/startseite/wettbewerb/URU1",
    "Peru Liga 1 Apertura": "https://www.transfermarkt.us/liga-1-apertura/startseite/wettbewerb/TDeA",
    "Paraguay Primera Divison Apertura": "https://www.transfermarkt.us/primera-division-apertura/startseite/wettbewerb/PR1A",
    "Bolivia Division Profesional Apertura": "https://www.transfermarkt.us/division-profesional-apertura/startseite/wettbewerb/B1AP",
    "Venezuela Liga Apertura": "https://www.transfermarkt.us/liga-futve-apertura/startseite/wettbewerb/VZ1A",
    "Copa Libertadores": "https://www.transfermarkt.us/copa-libertadores/teilnehmer/pokalwettbewerb/CLI/"
}


class Transfermarkt():

    # ==============================================================================================
    def get_valid_seasons(self, league: str) -> dict:
        """ Return valid seasons for the chosen league
        
        Parameters
        ----------
        league : str
            The league to gather valid seasons for
        
        Returns
        -------
        : dict
            {year str: year id, ...}
        """
        if not isinstance(league, str): 
            raise TypeError("`league` must be a string.")
        if league not in comps.keys():
            raise InvalidLeagueException(league, "Transfermarkt", list(comps.keys()))
        
        scraper = cloudscraper.CloudScraper()
        try:
            soup = BeautifulSoup(scraper.get(comps[league]).content, "html.parser")
            season_tags = soup.find("select", {"name": "saison_id"}).find_all("option")  # type: ignore
            valid_seasons = dict([(x.text, x["value"]) for x in season_tags])
            return valid_seasons
        finally:
            scraper.close()
        
    # ==============================================================================================
    def get_club_links(self, year: str, league: str) -> Sequence[str]:
        """ Gathers all Transfermarkt club URL"s for the chosen league season.
        
        Parameters
        ----------
        year : str
            See the :ref:`transfermarkt_year` `year` parameter docs for details.
        league : str
            League to scrape.
        
        Returns
        -------
        : list of str
            List of the club URLs
        """
        if not isinstance(year, str):
            raise TypeError("`year` must be a string.")
        valid_seasons = self.get_valid_seasons(league)
        if year not in valid_seasons.keys():
            raise InvalidYearException(year, league, list(valid_seasons.keys()))
        
        scraper = cloudscraper.CloudScraper()
        try:
            soup = BeautifulSoup(
                scraper.get(f"{comps[league]}/plus/?saison_id={valid_seasons[year]}").content,
                "html.parser"
            )
            items_table_tag = soup.find("table", {"class": "items"})
            if items_table_tag is None:
                warnings.warn(
                    f"No club links table found for {year} {league}. Returning empty list."
                )
                club_links = list()
            else:
                # club_els = items_table_tag.find_all("td", {"class": "hauptlink no-border-links"}) or 'links no-border-links hauptlink' # type: ignore
                club_els = items_table_tag.find_all("td", class_=lambda c: c in ["hauptlink no-border-links", "links no-border-links hauptlink"])
                club_links = [TRANSFERMARKT_ROOT + x.find("a")["href"] for x in club_els]
            return club_links
        finally:
            scraper.close()
    
    # ==============================================================================================
    def get_player_links(self, year: str, league: str) -> Sequence[str]:
        """ Gathers all Transfermarkt player URL"s for the chosen league season.
        
        Parameters
        ----------
        year : str
            See the :ref:`transfermarkt_year` `year` parameter docs for details.
        league : str
            League to scrape.
        
        Returns
        -------
        : list of str
            List of the player URLs
        """
        player_links = list()
        scraper = cloudscraper.CloudScraper()
        try:
            club_links = self.get_club_links(year, league)
            for club_link in tqdm(club_links, desc=f"{year} {league} player links"):
                soup = BeautifulSoup(scraper.get(club_link).content, "html.parser")
                player_table = soup.find("table", {"class": "items"})
                if player_table is not None:
                    player_els = player_table.find_all("td", {"class": "hauptlink"})  # type: ignore
                    p_links = [
                        TRANSFERMARKT_ROOT + x.find("a")["href"] for x in player_els
                        if x.find("a") is not None
                    ]
                    player_links += p_links
            return list(set(player_links))
        finally:
            scraper.close()
    
    # ==============================================================================================
    def get_match_links(self, year: str, league: str) -> Sequence[str]:
        """ Returns all match links for a given competition season.

        Parameters
        ----------
        year : str
            See the :ref:`transfermarkt_year` `year` parameter docs for details.
        league : str
            League to scrape.
        
        Returns
        -------
        : list of str
            List of the match URLs
        """
        valid_seasons = self.get_valid_seasons(league)
        fixtures_url = f"{comps[league].replace('startseite', 'gesamtspielplan')}/saison_id/{valid_seasons[year]}"
        scraper = cloudscraper.CloudScraper()
        try:
            soup = BeautifulSoup(scraper.get(fixtures_url).content, "html.parser")
            match_tags = soup.find_all("a", {"class": "ergebnis-link"})
            match_links = ["https://www.transfermarkt.us" + x["href"] for x in match_tags]
            return match_links
        finally:
            scraper.close()
    
    # ==============================================================================================
    def scrape_players(self, year: str, league: str) -> pd.DataFrame:
        """ Gathers all player info for the chosen league season.
        
        Parameters
        ----------
        year : str
            See the :ref:`transfermarkt_year` `year` parameter docs for details.
        league : str
            League to scrape.
        
        Returns
        -------
        : DataFrame
            Each row is a player and contains some of the information from their Transfermarkt
            player profile.
        """
        player_links = self.get_player_links(year, league)
        df = pd.DataFrame()
        for player_link in tqdm(player_links, desc=f"{year} {league} players"):
            player = self.scrape_player(player_link)
            df = pd.concat([df, player], axis=0, ignore_index=True)
        
        return df

    # ==============================================================================================
    def scrape_player(self, player_link: str) -> pd.DataFrame:
        """ Scrape a single player Transfermarkt link

        Parameters
        ----------
        player_link : str
            Valid player Transfermarkt URL

        Returns
        -------
        : DataFrame
            1-row dataframe with all of the player details
        """
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
                        "(KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
        }
        
        try:
            r = requests.get(player_link, headers=headers)
            r.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
            soup = BeautifulSoup(r.content, "html.parser")
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return pd.DataFrame()  # Return empty DataFrame on request failure
        
        # Name
        name = None
        name_tag = soup.find("h1", class_="data-header__headline-wrapper")
        if name_tag:
            name = name_tag.text.strip().split("\n")[-1]

        # Shirt number
        try:
            shirt_number_tag = soup.find("span", class_="data-header__shirt-number")
            shirt_number = int(shirt_number_tag.text.strip().replace("#", "")) if shirt_number_tag else None
        except ValueError:
            shirt_number = None

        # Value
        try:
            value_tag = soup.find("a", class_="data-header__market-value-wrapper")
            value = value_tag.text.split(" ")[0] if value_tag else None
            value_last_updated_tag = soup.find("a", class_="data-header__market-value-wrapper")
            value_last_updated = value_last_updated_tag.text.split("Last update: ")[-1] if value_last_updated_tag else None
        except AttributeError:
            value, value_last_updated = None, None

        # DOB and age
        dob_el = soup.find("span", itemprop="birthDate")
        if dob_el:
            dob_parts = dob_el.text.strip().split(" ")
            dob = " ".join(dob_parts[:3]) if len(dob_parts) >= 3 else None
            age = int(dob_parts[-1].replace("(", "").replace(")", "")) if dob_parts[-1].isdigit() else None
        else:
            dob, age = None, None

        # Height
        height_tag = soup.find("span", itemprop="height")
        if height_tag:
            height_str = height_tag.text.strip()
            height = float(height_str.replace(" m", "").replace(",", ".")) if height_str not in ["N/A", "- m"] else None
        else:
            height = None

        # Nationality and citizenships
        nationality = None
        nationality_el = soup.find("span", itemprop="nationality")
        if nationality_el:
            nationality = nationality_el.get_text(strip=True)

        citizenship = []
        citizenship_els = soup.find_all("span", class_="info-table__content info-table__content--bold")
        for el in citizenship_els:
            flag_els = el.find_all("img", class_="flaggenrahmen")
            citizenship.extend(el["title"] for el in flag_els if el.get("title"))

        # Position
        position = None
        position_el = soup.find("dd", class_="detail-position__position")
        if not position_el:
            position_els = [el for el in soup.find_all("li", class_="data-header__label") if "position" in el.text.lower()]
            position_el = position_els[0].find("span") if position_els else None
        if position_el:
            position = position_el.text.strip()

        try:
            other_positions = [
                el.text for el in soup.find("div", class_="detail-position__position").find_all("dd")
            ] if soup.find("div", class_="detail-position__position") else None
        except AttributeError:
            other_positions = None

        # Team
        team = None
        team_tag = soup.find("span", class_="data-header__club")
        if team_tag:
            team = team_tag.text.strip()

        # Extract additional data headers
        data_headers_labels = soup.find_all("span", class_="data-header__label")

        def extract_data_from_headers(keyword: str):
            results = [x.text.split(":")[-1].strip() for x in data_headers_labels if keyword.lower() in x.text.lower()]
            return results[0] if results else None

        last_club = extract_data_from_headers("last club")
        since_date = extract_data_from_headers("since")
        joined_date = extract_data_from_headers("joined")
        contract_expiration = extract_data_from_headers("contract expires")

        # Market value history
        market_value_history = None
        try:
            script = next(s for s in soup.find_all("script", type="text/javascript") if "var chart = new Highcharts.Chart" in str(s))
            values = [int(s.split(",")[0]) for s in str(script).split("y\":")[2:-2]]
            dates = [s.split("datum_mw\":")[-1].split(",\"x")[0].replace("\\x20", " ").replace("\"", "") for s in str(script).split("y\":")[2:-2]]
            market_value_history = pd.DataFrame({"date": dates, "value": values})
        except (StopIteration, IndexError, ValueError):
            market_value_history = None

        # Transfer History
        transfer_history = None
        try:
            rows = soup.find_all("div", class_="grid tm-player-transfer-history-grid")
            transfer_history = pd.DataFrame(
                [[s.strip() for s in row.get_text("\n").split("\n") if s] for row in rows],
                columns=["Season", "Date", "Left", "Joined", "MV", "Fee"]
            )
        except Exception as e:
            print(f"Error parsing transfer history: {e}")
            transfer_history = None

        # Create final player DataFrame
        player_data = {
            "Name": name,
            "Shirt number": shirt_number,
            "ID": player_link.split("/")[-1],
            "Value": value,
            "Value last updated": value_last_updated,
            "DOB": dob,
            "Age": age,
            "Height (m)": height,
            "Nationality": nationality,
            "Citizenship": citizenship,
            "Position": position,
            "Other positions": None if not other_positions else pd.DataFrame(other_positions),
            "Team": team,
            "Last club": last_club,
            "Since": since_date,
            "Joined": joined_date,
            "Contract expiration": contract_expiration,
            "Market value history": market_value_history,
            "Transfer history": transfer_history
        }

        return pd.DataFrame([player_data])
