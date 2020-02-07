import unittest
import os
import sys
import shutil

PAR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path.append(PAR_DIR)

from core import project as pr, fragment as fr
import download_examples


class Testing(unittest.TestCase):
    path = os.path.join('music', 'AJR-Weak.mp3')

    @classmethod
    def setUpClass(cls):
        download_examples.get_directory(PAR_DIR)
        pass

    def setUp(self):
        self.p = pr.Project()
        self.p.add_track(os.path.join(PAR_DIR, self.path))

    def test_adding_track(self):
        tracks = [e.filename for e in self.p.tracks]
        self.assertEqual(["AJR-Weak.mp3"], tracks)

    def test_adding_fragment(self):
        self.p.add_fragment("AJR-Weak.mp3")
        self.assertEqual("*unnamed0", self.p.fragments[0].name)
        self.assertIsInstance(self.p.fragments[0], fr.Fragment)

    def test_track_by_name(self):
        track = self.p.track_by_name("AJR-Weak.mp3")
        self.assertIsNotNone(track)
        self.assertEqual("AJR-Weak.mp3", track.filename)

    def test_addingDirectory(self):
        self.p.add_dir(os.path.join(PAR_DIR, 'music'))
        tracks = [e.filename for e in self.p.tracks]
        s = {
            '90s Dance Music-Scatman.mp3',
            'AJR-Weak.mp3',
            'Alan Walker-Darkside.mp3',
            'Avicii-Feeling Good.mp3',
            'Avicii-Wake Me Up.mp3',
        }
        self.assertSetEqual(s, set(tracks))

    def test_change_fragmentSpeed(self):
        self.p.add_fragment(0)
        frag = self.p.fragments[0]
        frag.speed = 0.5
        self.assertAlmostEqual(frag.project_length * frag.speed,
                               frag.track_length, delta=1e-5)

    def test_deleteFragment(self):
        self.p.add_fragment(self.p.tracks[0])
        self.assertEqual(1, len(self.p.fragments))
        self.p.del_fragment(0)
        self.assertEqual(0, len(self.p.fragments))

    def test_loadProject(self):
        path = os.path.join(PAR_DIR, 'tests/current.proj')
        p1 = pr.Project()
        p1.add_dir(os.path.join(PAR_DIR, 'music'))
        p1.add_fragment(0)
        p1.save_project(path)

        p2 = pr.Project()
        p2.load_project(path)
        tracks1 = [e.filename for e in p1.tracks]
        tracks2 = [e.filename for e in p2.tracks]

        self.assertSetEqual(set(tracks1), set(tracks2))

        os.remove(path)

    def test_clearProject(self):
        self.p.add_fragment(0)
        self.p.clear()
        self.assertEqual(0, len(self.p.fragments))
        self.assertEqual(0, len(self.p.tracks))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(os.path.join(PAR_DIR, 'music'))


if __name__ == "__main__":
    print('Downloading examples')
    download_examples.main()
    unittest.main()
