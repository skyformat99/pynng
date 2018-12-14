import pynng
import pytest
import time
import threading

# TODO: all sockets need timeouts


addr = 'tcp://127.0.0.1:13131'


def test_context_manager_works():
    # we have to grab a reference to the sockets so garbage collection doesn't
    # close the socket for us automatically.
    with pynng.Pair0(listen=addr) as s0:  # noqa
        pass
    # we should be able to do it again if the context manager worked
    with pynng.Pair0(listen=addr) as s1:  # noqa
        pass


def test_pair0():
    with pynng.Pair0(listen=addr, recv_timeout=100) as s0, \
            pynng.Pair0(dial=addr, recv_timeout=100) as s1:
        val = b'oaisdjfa'
        s1.send(val)
        assert s0.recv() == val


def test_pair1():
    with pynng.Pair1(listen=addr, recv_timeout=100) as s0, \
            pynng.Pair1(dial=addr, recv_timeout=100) as s1:
        val = b'oaisdjfa'
        s1.send(val)
        assert s0.recv() == val


def test_reqrep0():
    with pynng.Req0(listen=addr, recv_timeout=100) as req, \
            pynng.Rep0(dial=addr, recv_timeout=100) as rep:

        request = b'i am requesting'
        req.send(request)
        assert rep.recv() == request

        response = b'i am responding'
        rep.send(response)
        assert req.recv() == response

        with pytest.raises(pynng.BadState):
            req.recv()

        # responders can't send before receiving
        with pytest.raises(pynng.BadState):
            rep.send(b'I cannot do this why am I trying')


def test_pubsub0():
    with pynng.Sub0(listen=addr, recv_timeout=100) as sub, \
            pynng.Pub0(dial=addr, recv_timeout=100) as pub:

        sub.subscribe(b'')
        msg = b'i am requesting'
        time.sleep(0.04)
        pub.send(msg)
        assert sub.recv() == msg

        # TODO: when changing exceptions elsewhere, change here!
        # publishers can't recv
        with pytest.raises(pynng.NotSupported):
            pub.recv()

        # responders can't send before receiving
        with pytest.raises(pynng.NotSupported):
            sub.send(b"""I am a bold subscribing socket.  I believe I was truly
                         meant to be a publisher.  The world needs to hear what
                         I have to say!
                     """)
            # alas, it was not meant to be, subscriber.  Not every socket was
            # meant to publish.


def test_push_pull():
    received = {'pull1': False, 'pull2': False}
    with pynng.Push0(listen=addr) as push, \
            pynng.Pull0(dial=addr, recv_timeout=1000) as pull1, \
            pynng.Pull0(dial=addr, recv_timeout=1000) as pull2:

        def recv1():
            pull1.recv()
            received['pull1'] = True

        def recv2():
            pull2.recv()
            received['pull2'] = True

        # push/pull does round robin style distribution
        t1 = threading.Thread(target=recv1, daemon=True)
        t2 = threading.Thread(target=recv2, daemon=True)

        t1.start()
        t2.start()
        time.sleep(0.01)
        push.send(b'somewhere someone should see this')
        push.send(b'somewhereeeee')
        t1.join()
        t2.join()
        assert received['pull1']
        assert received['pull2']


def test_surveyor_respondent():
    with pynng.Surveyor0(listen=addr, recv_timeout=1000) as surveyor, \
            pynng.Respondent0(dial=addr, recv_timeout=1000) as resp1, \
            pynng.Respondent0(dial=addr, recv_timeout=2000) as resp2:
        query = b"hey how's it going buddy?"
        # wait for sockets to connect
        time.sleep(0.01)
        surveyor.send(query)
        assert resp1.recv() == query
        assert resp2.recv() == query
        resp1.send(b'not too bad I suppose')

        msg2 = b'''
            Thanks for asking.  It's been a while since I've had
            human contact; times have been difficult for me.  I woke up this
            morning and again could not find a pair of matching socks.  I know that
            a lot of people think it's worth it to just throw all your old socks
            out and buy like 12 pairs of identical socks, but that just seems so
            mundane.  Life is about more than socks, you know?  So anyway, since I
            couldn't find any socks, I went ahead and put banana peels on my
            feet.  They don't match *perfectly* but it's close enough.  Anyway
            thanks for asking, I guess I'm doing pretty good.
        '''
        resp2.send(msg2)
        resp = [surveyor.recv() for _ in range(2)]
        assert b'not too bad I suppose' in resp
        # if they're not the same
        assert msg2 in resp

        with pytest.raises(pynng.BadState):
            resp2.send(b'oadsfji')


def test_cannot_instantiate_socket_without_opener():
    with pytest.raises(TypeError):
        pynng.Socket()


def test_can_instantiate_socket_with_raw_opener():
    with pynng.Socket(opener=pynng.lib.nng_sub0_open_raw):
        pass


def test_can_pass_addr_as_bytes_or_str():
    with pynng.Pair0(listen=b'tcp://127.0.0.1:42421'), \
            pynng.Pair0(dial='tcp://127.0.0.1:42421'):
        pass


