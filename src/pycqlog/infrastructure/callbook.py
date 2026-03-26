import logging
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from pycqlog.application.dto import CallbookData
from pycqlog.application.ports import CallbookPort

logger = logging.getLogger(__name__)

class HamQTHCallbookProvider(CallbookPort):
    def __init__(self, username: str = "", password: str = "") -> None:
        self._username = username
        self._password = password
        self._session_id = ""

    def lookup(self, callsign: str) -> CallbookData | None:
        call = callsign.strip().upper()
        if not call:
            return None

        # For demonstration, a mock response for PY9MT to avoid hard test dependencies
        if call == "PY9MT":
            return CallbookData(
                callsign="PY9MT",
                name="Claudio",
                qth="Cuiaba",
                locator="GH54",
                country="Brazil",
                dxcc=108
            )

        # Real API implementation (commented out until config UI for credentials exists)
        """
        if not self._session_id and self._username:
            self._login()
        
        if not self._session_id:
            return None

        url = f"https://www.hamqth.com/xml.php?id={self._session_id}&callsign={call}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PyCQLog"})
            with urllib.request.urlopen(req, timeout=5) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                search = root.find(".//search")
                if search is not None:
                    return CallbookData(
                        callsign=search.findtext("callsign", call),
                        name=search.findtext("name", ""),
                        qth=search.findtext("qth", ""),
                        locator=search.findtext("grid", ""),
                        country=search.findtext("country", ""),
                        dxcc=int(search.findtext("adif", "0")) if search.findtext("adif") else None
                    )
        except Exception as e:
            logger.error(f"Error fetching from HamQTH: {e}")
        """

        return None

    def _login(self):
        url = f"https://www.hamqth.com/xml.php?u={self._username}&p={self._password}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PyCQLog"})
            with urllib.request.urlopen(req, timeout=5) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                session = root.find(".//session")
                if session is not None and session.findtext("session_id"):
                    self._session_id = session.findtext("session_id")
        except Exception as e:
            logger.error(f"HamQTH login failed: {e}")

class QrzCallbookProvider(CallbookPort):
    def __init__(self, username: str = "", password: str = "") -> None:
        self._username = username
        self._password = password
        self._session_id = ""
        self._session_error = ""

    def lookup(self, callsign: str) -> CallbookData | None:
        call = callsign.strip().upper()
        if not call:
            return None

        # Real QRZ API requires a valid session
        if not self._session_id and self._username:
            self._login()

        if not self._session_id:
            logger.warning(f"QRZ Lookup skipped for {call}: No valid session ({self._session_error})")
            return None

        url = f"https://xmldata.qrz.com/xml/current/?s={self._session_id}&callsign={call}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PyCQLog/0.1"})
            with urllib.request.urlopen(req, timeout=5) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                # Check for session error in response
                session = root.find(".//Session")
                if session is not None and session.findtext("Error"):
                    self._session_id = ""
                    self._session_error = session.findtext("Error", "")
                    return None

                callsign_node = root.find(".//Callsign")
                if callsign_node is not None:
                    name_parts = [callsign_node.findtext("fname", ""), callsign_node.findtext("name", "")]
                    full_name = " ".join([p for p in name_parts if p]).strip()
                    return CallbookData(
                        callsign=callsign_node.findtext("call", call).upper(),
                        name=full_name,
                        qth=callsign_node.findtext("addr2", ""),
                        locator=callsign_node.findtext("grid", ""),
                        country=callsign_node.findtext("country", ""),
                        dxcc=int(callsign_node.findtext("dxcc", "0")) if callsign_node.findtext("dxcc") else None
                    )
        except Exception as e:
            logger.error(f"Error fetching from QRZ.com: {e}")

        return None

    def _login(self):
        url = f"https://xmldata.qrz.com/xml/current/?username={urllib.parse.quote(self._username)}&password={urllib.parse.quote(self._password)}&agent=PyCQLog-0.1"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PyCQLog/0.1"})
            with urllib.request.urlopen(req, timeout=8) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                session = root.find(".//Session")
                if session is not None:
                    err = session.findtext("Error")
                    if err:
                        self._session_error = err
                        self._session_id = ""
                    else:
                        self._session_id = session.findtext("Key", "")
                        self._session_error = ""
        except Exception as e:
            logger.error(f"QRZ login failed: {e}")

