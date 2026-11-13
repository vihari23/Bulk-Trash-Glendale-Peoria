import tempfile
import unittest
from pathlib import Path
from datetime import date, timedelta
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from generate import read_reviewed,parse_glendale_page,generate
class CalendarTests(unittest.TestCase):
    def test_2026(self):
        a=read_reviewed()
        self.assertEqual(len(a),12)
        self.assertEqual(a[-2],date(2026,11,23))
        self.assertEqual(a[-1],date(2026,12,28))
    def test_no_unverified_year(self):
        self.assertEqual(parse_glendale_page("<h2>2026 Bulk Trash Schedule</h2>",2027),[])
    def test_reject_incomplete(self):
        self.assertEqual(parse_glendale_page("<h2>2027 Bulk Trash Schedule</h2><h3>Section 4</h3><li>January 4-8</li>",2027),[])
    def test_three_feeds(self):
        with tempfile.TemporaryDirectory() as d:
            info=generate(date(2026,11,13),Path(d),[])
            self.assertEqual(len(info),3)
            for filename,_,_ in info:
                data=(Path(d)/filename).read_bytes()
                self.assertTrue(data.startswith(b"BEGIN:VCALENDAR\r\n"))
                self.assertTrue(data.endswith(b"END:VCALENDAR\r\n"))
                self.assertTrue(all(len(x)<=75 for x in data.split(b"\r\n")))
                self.assertIn(b"DTSTART;TZID=America/Phoenix:",data)
            self.assertIn(b"20261123T080000",(Path(d)/"glendale-bulk-trash.ics").read_bytes())
            self.assertIn(b"BOOKING REMINDER ONLY",(Path(d)/"aloravita-bulk-trash.ics").read_bytes().replace(b"\r\n ",b""))
    def test_future_only_verified(self):
        with tempfile.TemporaryDirectory() as d:
            generate(date(2027,3,1),Path(d),[])
            s=(Path(d)/"glendale-bulk-trash.ics").read_bytes()
            self.assertIn(b"not a confirmed collection date",s.replace(b"\r\n ",b""))
            self.assertNotIn(b"Glendale bulk trash \xe2\x80\x94 collection week",s)
if __name__=="__main__":
    unittest.main()
