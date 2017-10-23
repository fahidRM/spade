import logging
from abc import ABCMeta, abstractmethod
from threading import Event

import asyncio

logger = logging.getLogger('spade.Behaviour')


class Behaviour(object, metaclass=ABCMeta):
    def __init__(self):
        self._aiothread = None
        self.agent = None
        self.template = None
        self._force_kill = Event()

        self.queue = None

    def set_aiothread(self, aiothread):
        """
        Links the behaviour with the event loop.
        Also creates the incoming messages queue.
        :param aiothread: the thread with the event loop
        :type aiothread: spade.agent.AioThread
        """
        self._aiothread = aiothread
        self.queue = asyncio.Queue(loop=self._aiothread.loop)

    def set_agent(self, agent):
        """
        links behaviour with its owner agent
        :param agent: the agent who owns the behaviour
        :type agent: spade.agent.Agent
        """
        self.agent = agent

    def set_template(self, template):
        """
        Sets the template that is used to match incoming
        messages with this behaviour.
        :param template: the template to match with
        :type template: spade.template.Template
        """
        self.template = template

    def match(self, message):
        """
        Matches a message with the behaviour's template
        :param message: the message to match with
        :type message: spade.messafe.Message
        :return: wheter the messaged matches or not
        :rtype: bool
        """
        if self.template:
            return self.template.match(message)
        return True

    def set(self, name, value):
        """
        Stores a knowledge item in the agent knowledge base.
        :param name: name of the item
        :type name: str
        :param value: value of the item
        :type value: object
        """
        self.agent.set(name, value)

    def get(self, name):
        """
        Recovers a knowledge item from the agent's knowledge base.
        :param name: name of the item
        :type name: str
        :return: the object retrieved or None
        :rtype: object
        """
        return self.agent.get(name)

    def start(self):
        """
        starts behaviour in the event loop
        """
        self._aiothread.submit(self._start())

    async def _start(self):
        """
        start coroutine. runs on_start coroutine and then
        runs the _step coroutine where the body of the behaviour
        is called.
        """
        await self.on_start()
        await self._step()

    def kill(self):
        """
        stops the behaviour
        """
        self._force_kill.set()
        logger.info("Killing behavior {}".format(self))

    def is_killed(self):
        """
        Checks if the behaviour was killed by means of the kill() method.
        :return: whether the behaviour is killed or not
        :rtype: bool
        """
        return self._force_kill.is_set()

    def done(self):
        """
        returns True if the behaviour has finished
        else returns False
        :return: whether the behaviour is finished or not
        :rtype: bool
        """
        return False

    async def on_start(self):
        """
        coroutine called before the behaviour is started.
        """
        pass

    async def on_end(self):
        """
        coroutine called after the behaviour is done or killed.
        """
        pass

    @abstractmethod
    async def run(self):
        """
        body of the behaviour.
        to be implemented by user
        """
        raise NotImplementedError

    async def _run(self):
        """
        function to be overload by more complex behaviours.
        in other case it just calls run() coroutine.
        """
        await self.run()

    async def _step(self):
        """
        main loop of the behaviour.
        checks whether behaviour is done or killed,
        ortherwise it calls run() coroutine.
        """
        while not self.done() and not self.is_killed():
            await self._run()
        await self.on_end()

    async def enqueue(self, message):
        await self.queue.put(message)

    async def send(self, msg):
        """
        Sends a message.
        :param msg: the message to be sent.
        :type msg: spade.message.Message
        """
        if not msg.sender:
            msg.sender = str(self.agent.jid)
            logger.debug(f"Adding agent's jid as sender to message: {msg}")
        aioxmpp_msg = msg.prepare()
        await self.agent.stream.send(aioxmpp_msg)

    async def receive(self, timeout=None):
        """
        receives a message for this behaviour.
        if timeout is not None it returns the message or "None"
        after timeout is done.
        :param timeout: number of seconds until return
        :type timeout: int
        :return: a Message or None
        :rtype: spade.message.Message
        """
        if timeout:
            coro = self.queue.get()
            try:
                msg = await asyncio.wait_for(coro, timeout=timeout)
            except asyncio.TimeoutError:
                msg = None
        else:
            try:
                msg = await self.queue.get_nowait()
            except asyncio.QueueEmpty:
                msg = None
        return msg


class OneShotBehaviour(Behaviour, metaclass=ABCMeta):
    """
    this behaviour is only executed once
    """

    def __init__(self):
        super().__init__()
        self._already_executed = False

    def done(self):
        if not self._already_executed:
            self._already_executed = True
            return False
        return True
