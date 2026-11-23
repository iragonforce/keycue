import unittest
import hashlib
from keycue.keymap import KEY_INDICES, LED_SEQUENCE_POSITIONS, normalize_key, packet_position
from keycue.protocol import build_transaction, colour_buffer


class TestKeyMapping(unittest.TestCase):
    def test_complete_mapping(self):
        self.assertEqual(len(KEY_INDICES), 84)
        self.assertEqual(set(KEY_INDICES.values()), set(range(84)))
        self.assertEqual(len(set(LED_SEQUENCE_POSITIONS)), 84)

    def test_physically_verified_vtf(self):
        self.assertEqual([packet_position(k) for k in ('V', 'T', 'F')], [70, 39, 54])
        self.assertEqual(normalize_key('cmd'), 'LSUPER')

    def test_invalid_key(self):
        with self.assertRaises(ValueError):
            normalize_key('F13')


class TestProtocol(unittest.TestCase):
    def test_exact_transaction_shape(self):
        actions = build_transaction({'V': (255,255,255), 'T': (255,255,255), 'F': (255,255,255)})
        self.assertEqual(len(actions), 25)
        self.assertEqual(sum(x.operation == 'write' for x in actions), 22)
        self.assertEqual(sum(x.operation == 'read' for x in actions), 3)
        self.assertTrue(all(len(x.data) == 64 for x in actions if x.operation == 'write'))
        writes = [x.data for x in actions if x.operation == 'write']
        self.assertEqual(writes[0][:2], b'\x04\x18')
        self.assertEqual(writes[1][:2], b'\x04\x13')
        self.assertEqual(writes[1][8], 18)
        self.assertEqual(writes[-2][:2], b'\x04\x02')
        self.assertEqual(writes[-1][:2], b'\x04\xf0')

    def test_vtf_payload_regression(self):
        # Frozen from a reconstruction of the user-confirmed 22-write script.
        actions = build_transaction({'V':(255,255,255),'T':(255,255,255),'F':(255,255,255)})
        data = b''.join(a.data for a in actions if a.operation == 'write')
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         '0c343d7a2a129a2f934a55aedb47c24f641623f3d33fd709b74262b674f1cba4')

    def test_only_three_keys_lit(self):
        data = colour_buffer({'V':(255,255,255),'T':(255,255,255),'F':(255,255,255)})
        self.assertEqual(len(data), 576)
        for pos in LED_SEQUENCE_POSITIONS:
            led = data[pos*4:pos*4+4]
            if pos in (70,39,54):
                self.assertEqual(led, b'\x80\xff\xff\xff')
            else:
                self.assertEqual(led, b'\x80\x00\x00\x00')

    def test_off_is_all_black(self):
        data = colour_buffer({})
        self.assertTrue(all(data[pos*4+1:pos*4+4] == b'\0\0\0' for pos in LED_SEQUENCE_POSITIONS))

    def test_bad_rgb_rejected(self):
        for value in ((256,0,0), (-1,0,0), (3.0,0,0), (1,2)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                colour_buffer({'V': value})

if __name__ == '__main__':
    unittest.main()
