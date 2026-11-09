"""Offline regression tests: execute real methods against a simulated TV."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'custom_components/samsungtv_smart/api/mobilebff.py'
LAYER = 's/setting.layer.gamemode'
LABELS = ['Apagado', 'Encendido', 'Automático']

class Lock:
    async def __aenter__(self): pass
    async def __aexit__(self, *args): pass

class Clock:
    def __init__(self): self.now = 0
    def time(self): return self.now
    def get_running_loop(self): return self
    async def sleep(self, delay): self.now += delay

class Element:
    def __init__(self, label):
        self.element_id = LAYER
        self.label = label
        self.dim = False
        self.params = {'id': LAYER, 'title': 'Modo Juego', 'subTitle': label}

class Layer:
    def __init__(self, current):
        self.elements = tuple(Element(label) for label in LABELS)
        self.current = current
    @property
    def current_element(self):
        return None if self.current is None else self.elements[self.current]

class TV:
    def __init__(self, current, behavior='cycle'):
        self.layers = {LAYER: Layer(current)}
        self._game_mode_lock = Lock()
        self.writes = 0
        self.behavior = behavior
        self.clock = Clock()
    @staticmethod
    def _ok(answer): return answer == {'response': {'status': 'ok'}}
    async def _request(self, request, params=None, **kwargs):
        layer = self.layers[LAYER]
        if request == 'get.settings.data':
            if self.behavior == 'lost_read' and self.writes: return None
            return {'id': request, 'response': []}
        self.writes += 1
        if self.behavior == 'reject': return None
        if self.behavior == 'cycle' or self.behavior == 'lost_read':
            layer.current = (layer.current + 1) % 3
        elif self.behavior == 'direct':
            layer.current = LABELS.index(params['subTitle'])
        elif self.behavior == 'changed_options':
            layer.elements[0].label = 'Changed'
        return {'response': {'status': 'ok'}}

# Compile only the two real methods; no HA import, sockets or real sleep.
tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
methods = [n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name in ('async_set_setting', '_set_cycling_game_mode')]

class CycleTests(unittest.TestCase):
    def run_target(self, current, target, behavior='cycle', missing=False, disabled=False):
        tv = TV(current, behavior)
        scope = {'asyncio': tv.clock, '_LOGGER': SimpleNamespace(debug=lambda *a: None)}
        for method in methods:
            exec(compile(ast.Module(body=[method], type_ignores=[]), str(SOURCE), 'exec'), scope)
            setattr(TV, method.name, scope[method.name])
        if missing: tv.layers[LAYER].current = None
        if disabled: tv.layers[LAYER].elements[target].dim = True
        coro = tv.async_set_setting(LAYER, target)
        try:
            with self.assertRaises(StopIteration) as stopped: coro.send(None)
            return tv, stopped.exception.value
        finally: coro.close()

    def test_every_source_target_pair(self):
        for source in range(3):
            for target in range(3):
                with self.subTest(source=source, target=target):
                    tv, ok = self.run_target(source, target)
                    self.assertTrue(ok)
                    self.assertEqual(tv.layers[LAYER].current, target)
                    self.assertEqual(tv.writes, (target-source) % 3)

    def test_no_repeated_write_without_observed_change(self):
        tv, ok = self.run_target(2, 1, 'stuck')
        self.assertFalse(ok)
        self.assertEqual(tv.writes, 1)

    def test_rejection_stops(self):
        tv, ok = self.run_target(2, 1, 'reject')
        self.assertFalse(ok)
        self.assertEqual(tv.writes, 1)

    def test_lost_read_stops(self):
        tv, ok = self.run_target(2, 1, 'lost_read')
        self.assertFalse(ok)
        self.assertEqual(tv.writes, 1)

    def test_changed_options_stop(self):
        tv, ok = self.run_target(2, 1, 'changed_options')
        self.assertFalse(ok)
        self.assertEqual(tv.writes, 1)

    def test_direct_selection_still_works(self):
        tv, ok = self.run_target(2, 1, 'direct')
        self.assertTrue(ok)
        self.assertEqual(tv.writes, 1)

    def test_unknown_or_dim_state_does_not_write(self):
        for kwargs in ({'missing': True}, {'disabled': True}):
            tv, ok = self.run_target(2, 1, **kwargs)
            self.assertFalse(ok)
            self.assertEqual(tv.writes, 0)

if __name__ == '__main__': unittest.main(verbosity=2)
