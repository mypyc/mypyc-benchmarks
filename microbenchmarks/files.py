"""Benchmarks for file-like objects."""

import os

from benchmarking import benchmark


@benchmark
def read_write_text() -> None:
    a = []
    for i in range(1000):
        a.append('Foobar-%d\n' % i)
        a.append(('%d-ab-asdfsdf-asdf' % i) * 2)
        a.append('yeah\n')
        a.append('\n')
    joined = ''.join(a)
    fnam = '__dummy.txt'
    try:
        for i in range(100):
            with open(fnam, 'w') as f:
                for s in a:
                    f.write(s)
            with open(fnam) as f:
                data = f.read()
            assert data == joined
    finally:
        if os.path.isfile(fnam):
            os.remove(fnam)


@benchmark
def readline() -> None:
    a = []
    for i in range(1000):
        a.append('Foobar-%d\n' % i)
        a.append(('%d-ab-asdfsdf-asdf' % i) * 2 + '\n')
        a.append('yeah\n')
        a.append('\n')
    fnam = '__dummy.txt'
    try:
        for i in range(50):
            with open(fnam, 'w') as f:
                for s in a:
                    f.write(s)
            for j in range(10):
                aa = []
                with open(fnam) as f:
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        aa.append(line)
                assert a == aa, aa
    finally:
        if os.path.isfile(fnam):
            os.remove(fnam)


@benchmark
def read_write_binary() -> None:
    a = []
    for i in range(1000):
        a.append(b'Foobar-%d\n' % i)
        a.append((b'%d-ab-asdfsdf-asdf' % i) * 2)
        a.append(b'yeah\n')
        a.append(b'\n')
    joined = b''.join(a)
    fnam = '__dummy.txt'
    try:
        for i in range(100):
            with open(fnam, 'wb') as f:
                for s in a:
                    f.write(s)
            with open(fnam, 'rb') as f:
                data = f.read()
            assert data == joined
    finally:
        if os.path.isfile(fnam):
            os.remove(fnam)


@benchmark
def read_write_binary_chunks() -> None:
    a = []
    for i in range(500):
        a.append(b'Foobar-%d\n' % i)
        a.append((b'%d-ab-asdfsdf-asdf' % i) * 2)
        a.append(b'yeah\n')
        a.append(b'\n')
    joined = b''.join(a)
    i = 0
    size = 2048
    chunks = []
    while i < len(joined):
        chunks.append(joined[i : i + size])
        i += size
    assert len(chunks) == 14, len(chunks)

    fnam = '__dummy.txt'
    try:
        for i in range(1000):
            with open(fnam, 'wb') as f:
                for chunk in chunks:
                    f.write(chunk)
            with open(fnam, 'rb') as f:
                chunks2 = []
                while True:
                    chunk = f.read(size)
                    if not chunk:
                        break
                    chunks2.append(chunk)
            assert chunks == chunks2
    finally:
        if os.path.isfile(fnam):
            os.remove(fnam)


@benchmark
def read_write_chars() -> None:
    fnam = '__dummy.txt'
    try:
        for i in range(200):
            with open(fnam, 'w') as f:
                for s in range(1000):
                    f.write('a')
                    f.write('b')
                    f.write('c')
            n = 0
            with open(fnam) as f:
                while True:
                    ch = f.read(1)
                    if not ch:
                        break
                    n += 1

            assert n == 3000, n
    finally:
        if os.path.isfile(fnam):
            os.remove(fnam)


@benchmark
def read_write_small_files() -> None:
    fnam = '__dummy%d.txt'
    num_files = 10
    try:
        for i in range(500):
            for i in range(num_files):
                with open(fnam % i, 'w') as f:
                    f.write('yeah\n')
            for i in range(num_files):
                with open(fnam % i) as f:
                    data = f.read()
            assert data == 'yeah\n'
    finally:
        for i in range(num_files):
            if os.path.isfile(fnam % i):
                os.remove(fnam % i)


@benchmark
def read_write_close() -> None:
    fnam = '__dummy%d.txt'
    num_files = 10
    try:
        for i in range(500):
            for i in range(num_files):
                f = open(fnam % i, 'w')
                f.write('yeah\n')
                f.close()
            for i in range(num_files):
                f = open(fnam % i)
                data = f.read()
                f.close()
            assert data == 'yeah\n'
    finally:
        for i in range(num_files):
            if os.path.isfile(fnam % i):
                os.remove(fnam % i)
