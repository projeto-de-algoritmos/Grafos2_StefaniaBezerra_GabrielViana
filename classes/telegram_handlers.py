#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import sqlalchemy
from telegram import ReplyKeyboardRemove
from db import User
import db
from classes.services import Services
import twitter
from classes.graph import Graph
from itertools import islice

TUTORIAL = "https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/"

HELP = """
 /new NAME
 /delete ID
 /list

 /help
 /help_github_token
"""

FORMAT = '%(asctime)s -- %(levelname)s -- %(module)s %(lineno)d -- %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
LOGGER = logging.getLogger('root')
LOGGER.info("Running %s", sys.argv[0])


class Handler(object):
    def __init__(self):
        self.services = Services()

    @classmethod
    def auth(cls):
        return twitter.Api(consumer_key='',
                           consumer_secret='',
                           access_token_key='',
                           access_token_secret='')

    @classmethod
    def __delete_dependency(cls, update, user):
        for i in user.dependencies.split(',')[:-1]:
            i = int(i)
            query_loop = db.session.query(User).filter_by(
                id=i, chat=update.message.chat_id)
            user_loop = query_loop.one()
            user_loop.parents = user_loop.parents.replace(
                '{},'.format(user.id), '')
        user.dependencies = ''

    def __set_dependency(self, depids, update, user, bot):
        for depid in depids[1:]:
            if depid.isdigit():
                depid = int(depid)
                query = db.session.query(User).filter_by(id=depid,
                                                         chat=update.message.chat_id)
                try:
                    userdep = query.one()
                    userdep.parents += str(user.id) + ','
                except sqlalchemy.orm.exc.NoResultFound:
                    self.services.not_found_message(bot, update, depid)
                    continue

                deplist = user.dependencies.split(',')
                LOGGER.info("Deplist %s", deplist)
                if not self.services.a_is_in_b(update, depid, user):
                    user.dependencies += str(depid) + ','
                    bot.send_message(
                        chat_id=update.message.chat_id,
                        text="User {} dependencies up to date".format(depid))
                else:
                    bot.send_message(chat_id=update.message.chat_id,
                                     text="{} is dependence on some of these numbers.".format(depid))
            else:
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="All dependencies ids must be numeric, and not {}"
                    .format(depid))

    @classmethod
    def start(cls, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Welcome! Here is a list of things you can do.")
        bot.send_message(chat_id=update.message.chat_id,
                         text="{}".format(HELP))

    @classmethod
    def new(cls, bot, update, args):
        
        param1 = args[0]
        # param2 = args[1]
        # user = User(chat=update.message.chat_id, screen_name='{}'.format(text),
        #             friends='', tweet_id='')

        api = cls.auth()

        user_info1 = api.GetUser(screen_name=param1)
        # user_info2 = api.GetUser(screen_name=param2)
        friends1 = api.GetFriends(screen_name=param1)
        # friends2 = api.GetFriends(screen_name=param2)
        # print([s.text for s in statuses])

        graph = Graph()
        graph2 = Graph()
        # db.session.add(user)
        # db.session.commit()

        user_ids = []
        for s in islice(friends1, 5):
            current_friend_id = s.AsDict().get('id')
            print(current_friend_id)

            graph.add_vertex(current_friend_id)
            graph.add_edge({
                    user_info1.AsDict().get('id'), 
                    current_friend_id
                })

            # friends_of_current_friend = api.GetFriends(screen_name=s.AsDict().get('screen_name'))
            # for s in friends_of_current_friend:
            #     graph.add_edge({
            #         current_friend_id,
            #         s.AsDict().get('id')
            #     })
            # user_id = s.AsDict().get('id')
            # user_ids.append(user_id)

        # for s in friends2:
        #     graph.add_vertex(s.AsDict().get('id'))
        #     graph2.add_edge({
        #             user_info2.AsDict().get('id'), 
        #             s.AsDict().get('id')
        #         })
            # user_id = s.AsDict().get('id')
            # user_ids.append(user_id)

        # for user_id in user_ids:
        #     current = api.GetUser(user_id=user_id)
            

        print(graph.edges())
        print('\n ---------------------------------------------------------------------------------------- \n')
        print(graph2.edges())

        bot.send_message(chat_id=update.message.chat_id,
                         text="abigo stoaki:" + str())

    def echo(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text="I'm sorry, {}. I'm afraid I can't do {}."
                         .format(self.services.get_name(update), update.message.text))
        bot.send_message(chat_id=update.message.chat_id,
                         text="{}".format(HELP))

    @classmethod
    def help(cls, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Welcome! Here is a list of things you can do.")
        bot.send_message(chat_id=update.message.chat_id,
                         text="{}".format(HELP))

    def delete(self, bot, update, args):
        for i in args:
            if i.isdigit():
                user_id = int(i)
                user_id = int(args[0])
                query = db.session.query(User).filter_by(
                    id=user_id, chat=update.message.chat_id)
                try:
                    user = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    self.services.not_found_message(bot, update, user_id)
                    return
                for each_user in user.dependencies.split(',')[:-1]:
                    each_query = db.session.query(User).filter_by(
                        id=int(each_user), chat=update.message.chat_id)
                    each_user = each_query.one()
                    each_user.parents = each_user.parents.replace(
                        '{},'.format(user.id), '')
                db.session.delete(user)
                db.session.commit()
                bot.send_message(chat_id=update.message.chat_id,
                                 text="User [[{}]] deleted".format(user_id))
            else:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="You must inform the user id")

    def list(self, bot, update):
        message = ''

        message += '📋 User List\n'
        query = db.session.query(User).filter_by(
            friends='', chat=update.message.chat_id).order_by(User.id)
        for user in query.all():
            icon = '🆕'

            message += '[[{}]] {} {}\n'.format(user.id, icon, user.screen_name)
            message += self.services.deps_text(user=user,
                                               chat=update.message.chat_id)

        bot.send_message(chat_id=update.message.chat_id, text=message)
        message = ''

        message += '📝 _Status_\n'
        query = db.session.query(User).filter_by(
            status='TODO', chat=update.message.chat_id).order_by(User.id)
        message += '\n🆕 *TODO*\n'
        for user in query.all():
            if user.duedate != None:
                message += '[[{}]] {} -- Delivery date: {}\n'.format(
                    user.id, user.name, user.duedate)
            else:
                message += '[[{}]] {}\n'.format(user.id, user.name)
        query = db.session.query(User).filter_by(
            status='DOING', chat=update.message.chat_id).order_by(User.id)
        message += '\n🔘 *DOING*\n'
        for user in query.all():
            message += '[[{}]] {}\n'.format(user.id, user.name)
        query = db.session.query(User).filter_by(
            status='DONE', chat=update.message.chat_id).order_by(User.id)
        message += '\n✔️ *DONE*\n'
        for user in query.all():
            message += '[[{}]] {}\n'.format(user.id, user.name)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    @classmethod
    def show_priority(cls, bot, update):
        message = ''
        query = db.session.query(User).filter_by(
            chat=update.message.chat_id).order_by(User.id)
        for user in query.all():
            if user.priority == '':
                message += "[[{}]] {} doesn't have priority {}\n".format(user.id, user.name.upper(),
                                                                         user.priority.upper())
            else:
                message += '[[{}]] {} | priority {}\n'.format(user.id, user.name.upper(),
                                                              user.priority.upper())
        bot.send_message(chat_id=update.message.chat_id, text=message)
