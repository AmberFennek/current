from evennia import default_cmds, CmdSet
from past.builtins import cmp
from django.conf import settings
from evennia.comms.models import ChannelDB, Msg
from evennia.utils import create, utils, evtable
from evennia.utils.utils import make_iter, class_from_module


class MailCmdSet(CmdSet):
    key = 'mailbox'

    def at_cmdset_creation(self):
        """Add command to the set - this set will be attached to the mailbox object (item or room)."""
        self.add(CmdMail())


class CmdMail(default_cmds.MuxCommand):
    """
    Mail a private letter to another character or
    show your last <number> of letters (default is 5)
    Usage:
      mail[/switches] [<player>,<player>,... = <message>]
      mail <number>
    Options:
      last - shows your last correspondence.
    """

    key = 'mail'
    locks = 'cmd:not pperm(mail_banned) and at_home()'
    help_category = 'Communication'

    player_caller = True

    def func(self):
        """Implement function using the Msg methods"""
        # Since player_caller is set above, this will be a Player.
        char = self.character

        # get the messages we've sent (not to channels)
        sent_messages = Msg.objects.get_messages_by_sender(char, exclude_channel_messages=True)
        # get last messages we've got
        recd_messages = Msg.objects.get_messages_by_receiver(char)

        if 'last' in self.switches:
            if sent_messages:
                recv = ', '.join('%s%s|n' % (obj.STYLE, obj.key) for obj in sent_messages[-1].receivers)
                self.msg("You last mailed |w%s|n: |w%s" % (recv, sent_messages[-1].message))
            else:
                self.msg("You haven't mailed anyone yet.")
            return

        if not self.args or not self.rhs:
            mail = sent_messages + recd_messages
            mail.sort(lambda x, y: cmp(x.date_sent, y.date_sent))

            number = 5
            if self.args:
                try:
                    number = int(self.args)
                except ValueError:
                    self.msg("Usage: mail [<character> = msg]")
                    return

            if len(mail) > number:
                mail_last = mail[-number:]
            else:
                mail_last = mail
            template = "|w%s|n |w%s|n to |w%s|n: %s"
            mail_last = "\n ".join(template %
                                   (utils.datetime_format(mail.date_sent),
                                    ', '.join('%s%s|n' % (obj.STYLE, obj.key) for obj in mail.senders),
                                    ', '.join(['%s%s|n' % (obj.STYLE, obj.key) for obj in mail.receivers]),
                                    mail.message) for mail in mail_last)
            if mail_last:
                string = "Your latest letters:\n %s" % mail_last
            else:
                string = "You haven't mailed anyone yet."
            self.msg(string)
            return
        if not self.lhs:  # Send mode
            if sent_messages:  # If no recipients provided, then default to the last character mailed.
                receivers = sent_messages[-1].receivers
            else:
                self.msg("Who do you want to mail?")
                return
        else:  # Build a list of comma-delimited recipients.
            receivers = self.lhslist

        rec_objs = []
        received = []
        r_strings = []
        for receiver in set(receivers):
            if isinstance(receiver, basestring):
                c_obj = char.search(receiver, global_search=True, exact=True)
            elif hasattr(receiver, 'location'):
                c_obj = receiver
            else:
                self.msg("Who do you want to mail?")
                return
            if c_obj:
                if not c_obj.access(char, 'mail'):
                    r_strings.append("You are not able to mail %s." % c_obj)
                    continue
                rec_objs.append(c_obj)

        if not rec_objs:
            self.msg("No one found to mail.")
            return

        header = '|mMessage|n from %s%s:|n ' % (char.STYLE, char.key)
        message = self.rhs.strip()

        if message.startswith(':'):  # Format as pose if message begins with a :
            message = "%s%s|n %s" % (char.STYLE, char.key, message.strip(':'))

        create.create_message(char, message, receivers=rec_objs)

        for c_obj in rec_objs:  # TODO: Notify character of mail delivery. (birdseed)
            if hasattr(c_obj, 'sessions') and not c_obj.sessions.count():
                r_strings.append("%s is offline." % received[-1])
            else:  # Tell the receiving characters about receiving a letter if they are online.
                c_obj.msg('%s %s' % (header, message))
            received.append('%s%s|n' % (c_obj.STYLE, c_obj.key))

        if r_strings:
            self.msg("\n".join(r_strings))
        stamp_count = len(rec_objs)
        stamp_plural = 'a stamp' if stamp_count == 1 else '%i stamps' % stamp_count
        char.location.msg_contents('|g%s|n places %s on an envelope and slips it into the %s%s|n mailbox.'
                                   % (char.key, stamp_plural, char.STYLE, char.location), exclude=char)
        self.msg('Mail delivery costs %s.' % stamp_plural)
        self.msg("You mailed %s: '%s'." % (', '.join(received), message))
