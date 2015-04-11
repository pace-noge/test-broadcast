from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import BroadcastTextMessage
import threading
import logging
logger = logging.getLogger(__name__)

class SendBroadcastLayer(YowInterfaceLayer):

    PROP_MESSAGES = "org.openwhatsapp.yowsup.prop.sendclient.queue" #list of (jid, message) tuples

    def __init__(self):
        super(SendBroadcastLayer, self).__init__()
        self.ackQueue = []
        self.lock = threading.Condition()
        self.jidAliases = {
            # "NAME": "PHONE@s.whatsapp.net"
        }

    def aliasToJid(self, calias):
        for alias, ajid in self.jidAliases.items():
            if calias.lower() == alias.lower():
                return self.normalizeJid(ajid)

        return self.normalizeJid(calias)

    def jidToAlias(self, jid):
        for alias, ajid in self.jidAliases.items():
            if ajid == jid:
                return alias
        return jid

    def normalizeJid(self, number):
        if '@' in number:
            return number
        elif "-" in number:
            return "%s@g.us" % number

        return "%s@s.whatsapp.net" % number

    @ProtocolEntityCallback("success")
    def onSuccess(self, successProtocolEntity):
        self.lock.acquire()
        for target in self.getProp(self.__class__.PROP_MESSAGES, []):
            phone, message = target
            jids = [self.aliasToJid(number) for number in phone.split(',')]
            outgoingMessage = BroadcastTextMessage(jids, message)
            self.ackQueue.append(outgoingMessage.getId())
            self.toLower(outgoingMessage)
        self.lock.release()

    @ProtocolEntityCallback("ack")
    def onAck(self, entity):
        self.lock.acquire()
        if entity.getId() in self.ackQueue:
            self.ackQueue.pop(self.ackQueue.index(entity.getId()))

        if not len(self.ackQueue):
            self.lock.release()
            logger.info("Message sent")
            raise KeyboardInterrupt()

        self.lock.release()
