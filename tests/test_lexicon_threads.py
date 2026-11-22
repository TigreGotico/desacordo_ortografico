from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from desacordo_ortografico.lexicon import Lexicon


def test_threads_reading_a_fresh_lexicon_see_the_whole_word_set():
    expected = len(Lexicon().wordset)
    lexicon = Lexicon()
    barrier = Barrier(6)

    def size() -> int:
        barrier.wait()
        return len(lexicon.wordset)

    with ThreadPoolExecutor(6) as pool:
        sizes = list(pool.map(lambda _: size(), range(6)))
    assert sizes == [expected] * 6
