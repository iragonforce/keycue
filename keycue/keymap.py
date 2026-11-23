"""Legacy K2 LED mapping; V/T/F positions physically verified 2026-11-22.

Mapping based on WestSmit/Artemis.Plugins.KeychronK2.
"""
from __future__ import annotations

# LED ordinal -> position in a 576-byte colour table (four bytes per position).
LED_SEQUENCE_POSITIONS: tuple[int, ...] = (
    143,18,34,50,66,81,2,19,82,3,20,35,51,67,83,
    4,21,36,52,68,5,22,37,53,69,6,23,38,54,70,
    7,24,39,55,71,84,8,25,40,56,72,9,26,41,57,
    73,10,27,42,58,74,11,28,43,59,75,85,12,29,
    44,60,76,86,13,30,45,61,77,87,14,31,46,88,
    15,47,63,78,89,16,32,48,64,79,90,
)

# Logical key names -> LED ordinals, not packet positions.
KEY_INDICES: dict[str, int] = {
    'ESC':0,'F1':6,'F2':9,'F3':15,'F4':20,'F5':25,'F6':30,
    'F7':36,'F8':41,'F9':46,'F10':51,'F11':57,'F12':63,
    'PRTSC':69,'HOME':81,'PGUP':79,'GRAVE':1,
    '1':7,'2':10,'3':16,'4':21,'5':26,'6':31,'7':37,
    '8':42,'9':47,'0':52,'MINUS':58,'EQUAL':64,
    'BACKSPACE':70,'DELETE':73,'TAB':2,
    'Q':11,'W':17,'E':22,'R':27,'T':32,'Y':38,'U':43,
    'I':48,'O':53,'P':59,'LBRACKET':65,'RBRACKET':71,'BACKSLASH':74,
    'CAPS':3,'A':12,'S':18,'D':23,'F':28,'G':33,'H':39,
    'J':44,'K':49,'L':54,'SEMICOLON':60,'APOSTROPHE':66,
    'ENTER':75,'END':82,'LSHIFT':4,'Z':13,'X':19,
    'C':24,'V':29,'B':34,'N':40,'M':45,'COMMA':50,
    'DOT':55,'SLASH':61,'RSHIFT':67,'UP':76,'PGDN':80,
    'LCTRL':5,'LSUPER':8,'LALT':14,'SPACE':35,'RALT':56,
    'FN':62,'RCTRL':68,'LEFT':72,'DOWN':77,'RIGHT':83,
    'LIGHT':78,
}

KEY_ALIASES = {
    'ESCAPE':'ESC','RETURN':'ENTER','DEL':'DELETE',
    'BKSP':'BACKSPACE','BACKTICK':'GRAVE','TILDE':'GRAVE',
    'PAGEUP':'PGUP','PAGEDOWN':'PGDN','PERIOD':'DOT',
    'PRINTSCREEN':'PRTSC','LGUI':'LSUPER','SUPER':'LSUPER',
    'WIN':'LSUPER','CMD':'LSUPER','CONTROL':'LCTRL',
}
assert len(LED_SEQUENCE_POSITIONS) == 84
assert len(KEY_INDICES) == 84
assert set(KEY_INDICES.values()) == set(range(84))
assert len(set(LED_SEQUENCE_POSITIONS)) == 84
assert max(LED_SEQUENCE_POSITIONS) < 144


def normalize_key(key: str) -> str:
    k = key.strip().upper()
    k = KEY_ALIASES.get(k, k)
    if k not in KEY_INDICES:
        raise ValueError(f'Unknown K2 key {key!r}; use `keycue keys`')
    return k


def packet_position(key: str) -> int:
    return LED_SEQUENCE_POSITIONS[KEY_INDICES[normalize_key(key)]]
