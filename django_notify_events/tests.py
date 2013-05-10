from django.utils import unittest
from models import Events, Subscriptions, Notifications
from django.contrib.auth.models import User
import json
from django.core.exceptions import ObjectDoesNotExist
import time


class NotifyTestCases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        #create new user this will act as follower
        cls.follower = User.objects.create_user('follower', 'follower@test.com', 'pass')

        #create new user this will act as follower
        cls.follower2 = User.objects.create_user('follower2', 'follower2@test.com', 'pass')

        #create new user this will act as actor
        cls.actor = User.objects.create_user('actor', 'actor@test.com', 'pass')

    def test_create_one_event(self):
        event = Events.create_event("w_e_random1", "is random", "c_random")

        self.assertEqual(event.name, "w_e_random1")
        self.assertEqual(event.description, "is random")
        self.assertEqual(event.category, "c_random")

        #get subs for users
        f_subs = Subscriptions.objects.filter(follower=self.follower, event=event)
        self.assertEqual(len(f_subs), 1)
        self.assertEqual(f_subs[0].event, event)
        self.assertEqual(f_subs[0].period, 0)
        self.assertEqual(f_subs[0].unfollow_actors, "")
        self.assertEqual(f_subs[0].rules, "[[],[],[],[]]")
        self.assertEqual(f_subs[0].notify_channels, None)

        a_subs = Subscriptions.objects.filter(follower=self.actor, event=event)
        self.assertEqual(len(a_subs), 1)
        self.assertEqual(a_subs[0].event, event)
        self.assertEqual(a_subs[0].period, 0)
        self.assertEqual(f_subs[0].unfollow_actors, "")
        self.assertEqual(f_subs[0].rules, "[[],[],[],[]]")
        self.assertEqual(a_subs[0].notify_channels, None)

    def test_try_create_event_twice_or_more(self):
        event = Events.create_event("x_e_random1", "is random", "c_random")
        event = Events.create_event("x_e_random1", "is random", "c_random")
        event = Events.create_event("x_e_random1", "is random", "c_random")
        event = Events.create_event("x_e_random1", "is random", "c_random")
        event = Events.create_event("x_e_random1", "is random", "c_random")

        self.assertEqual(event.name, "x_e_random1")
        self.assertEqual(event.description, "is random")
        self.assertEqual(event.category, "c_random")

        #get subs for users
        f_subs = Subscriptions.objects.filter(follower=self.follower, event=event)
        self.assertEqual(len(f_subs), 1)
        self.assertEqual(f_subs[0].event, event)
        self.assertEqual(f_subs[0].period, 0)
        self.assertEqual(f_subs[0].notify_channels, None)

        a_subs = Subscriptions.objects.filter(follower=self.actor, event=event)
        self.assertEqual(len(a_subs), 1)
        self.assertEqual(a_subs[0].event, event)
        self.assertEqual(a_subs[0].period, 0)
        self.assertEqual(a_subs[0].notify_channels, None)

    def test_create_event_min_period(self):
        event1 = Events.create_event("e_random1", "is random", "c_random_test_create_event_min_period")
        f_subs1 = Subscriptions.objects.filter(follower=self.follower, event=event1)
        f_subs1[0].period = 50
        f_subs1[0].save()

        event2 = Events.create_event("e_random2", "is random", "c_random_test_create_event_min_period")
        f_subs2 = Subscriptions.objects.filter(follower=self.follower, event=event2)
        f_subs2[0].period = 70
        f_subs2[0].save()

        event3 = Events.create_event("e_random3", "is random", "c_random_test_create_event_min_period")
        f_subs3 = Subscriptions.objects.filter(follower=self.follower, event=event3)
        f_subs3[0].period = 2
        f_subs3[0].save()

        event4 = Events.create_event("e_random4", "is random", "c_random_test_create_event_min_period")
        f_subs4 = Subscriptions.objects.filter(follower=self.follower, event=event4)
        self.assertEqual(f_subs4[0].period, 2)

        event5 = Events.create_event("e_random5", "is random", "c_random_test_create_event_min_period_2")
        f_subs5 = Subscriptions.objects.filter(follower=self.follower, event=event5)
        self.assertEqual(f_subs5[0].period, 0)

    def test_check_period(self):
        event1 = Events.create_event("www_e_random1", "is random ", "c_random_test_check_period")
        f_subs1 = Subscriptions.objects.get(follower=self.follower, event=event1)
        f_subs1.period = 3600
        f_subs1.save()

        name = "www_e_random1"
        category = "c_random"
        description = "is random"
        object_type = "blog_post"
        object_id = "00"
        actor = self.actor
        extra_data = {"test": "ok"}

        Events.add(**locals())

        notify = Notifications.objects.get(user=self.follower, event=event1)
        self.assertTrue((int(time.time())+3600 - notify.dispatch_time) < 10)

    def test_filter(self):
        event1 = Events.create_event("www_e_random1", "is random ", "c_random_test_check_period")
        f_subs1 = Subscriptions.objects.get(follower=self.follower, event=event1)
        f_subs1.period = 3600
        f_subs1.save()

        name = "test_filter"
        category = "c_random"
        description = "is random"
        object_type = "blog_post"
        object_id = "00"
        actor = self.actor
        extra_data = {"test": "ok"}

        def filter(*args, **kwargs):
            if kwargs["subscription"].follower == self.follower:
                return False
            return True

        event = Events.add(**locals())

        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.follower, "event": event})



    def test_new_user_subs_old_events(self):

        event1 = Events.create_event("e_random1", "is random", "c_random")
        event2 = Events.create_event("e_random2", "is random", "c_random")
        event2.active = False
        event2.save()
        event3 = Events.create_event("e_random3", "is random", "c_random")

        self.new_user = User.objects.create_user('new_user', 'new_user@test.com', 'pass')

        Subscriptions.objects.filter(follower=self.new_user, event=event3)
        Subscriptions.objects.filter(follower=self.new_user, event=event1)
        Subscriptions.objects.filter(follower=self.new_user, event=event2)

    def test_new_event_not_auto_subs(self):
        name = "P_e_random2"
        category = "Blog"
        description = "New blog entry is created"
        object_type = "blog_post"
        object_id = "00"
        actor = self.actor
        extra_data = {"test": "ok"}
        auto_subscription = False

        Events.add(**locals())
        event1 = Events.create_event("P_e_random1", "is random", "c_random", False)
        event2 = Events.objects.get(name=name)

        self.assertEqual(len(Subscriptions.objects.filter(follower=self.follower2, event=event1)), 0)
        self.assertEqual(len(Subscriptions.objects.filter(follower=self.follower2, event=event2)), 0)
        self.assertEqual(len(Subscriptions.objects.filter(follower=self.actor, event=event1)), 0)
        self.assertEqual(len(Subscriptions.objects.filter(follower=self.actor, event=event2)), 0)
        self.assertEqual(len(Subscriptions.objects.filter(follower=self.follower, event=event1)), 0)
        self.assertEqual(len(Subscriptions.objects.filter(follower=self.follower, event=event2)), 0)

    def test_notification_with_new_event(self):
        """
            test new event when this not exist in the db
        """
        name = "test_notification_with_new_event"
        category = "Blog_test_notification_with_new_event"
        description = "New blog entry is created"
        object_type = "blog_post"
        object_id = "00"
        actor = self.actor
        extra_data = {"test": "ok"}

        Events.add(**locals())

        event = Events.create_event(name, description, category)

        #get notifications
        Notifications.objects.get(user=self.follower2, event=event)
        notify = Notifications.objects.get(user=self.follower, event=event)

        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.actor, "event": event})

        self.assertEqual(notify.actor, self.actor)
        self.assertEqual(notify.object_id, object_id)
        self.assertEqual(notify.object_type, object_type)
        self.assertEqual(notify.notify_channel, None)
        self.assertEqual(notify.extra_data, json.dumps(extra_data))

    def test_notification_with_new_event_and_notify_channel(self):
        name = "new_event_notify"
        category = "Blog"
        description = "New blog entry is created"
        object_type = "blog_post"
        object_id = "00"
        actor = self.actor
        extra_data = {}
        notify_channel = "email"

        Events.add(**locals())

        event = Events.create_event(name, description, category)

        #get notifications
        Notifications.objects.get(user=self.follower2, event=event)
        notify = Notifications.objects.get(user=self.follower, event=event)
        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.actor, "event": event})

        self.assertEqual(notify.actor, self.actor)
        self.assertEqual(notify.object_id, object_id)
        self.assertEqual(notify.object_type, object_type)
        self.assertEqual(notify.notify_channel, notify_channel)
        self.assertEqual(notify.extra_data, json.dumps(extra_data))

    def test_notification_with_event_no_active(self):
        name = "new_event_no_active"
        category = "Blog"
        description = "New blog entry is created"
        object_type = "blog_post"
        object_id = "00"
        actor = self.actor
        extra_data = {}
        notify_channel = "email"
        event_params = locals()
        event = Events.create_event(name, description, category)
        event.active = False
        event.save()
        Events.add(**event_params)

        #get notifications
        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.follower, "event": event})

        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.follower2, "event": event})

        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.actor, "event": event})

    def test_notification_with_category_no_active(self):
        name = "new_event_c1"
        category = "Blog"
        description = "New blog entry is created"
        object_type = "blog_post"
        object_id = "00"
        actor = self.actor,
        extra_data = {}
        notify_channel = "email"
        event_params1 = locals()
        event1 = Events.create_event(name, description, category)

        event2 = Events.create_event("new_event_c2", description, category)

        Events.deactivate_category(category)

        Events.add(**event_params1)
        event_params1["name"] = "new_event_c2"
        Events.add(**event_params1)

        #get notifications
        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.follower, "event": event1})

        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.follower2, "event": event1})

        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.actor, "event": event1})

        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.follower, "event": event2})

        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.follower2, "event": event2})

        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.actor, "event": event2})

    def test_notification_with_event_twice_or_more(self):
        name = "new_event_two_or_more"
        category = "Blog"
        description = "New blog entry is created"
        object_type = "blog_post"
        object_id = "00"
        actor = self.actor
        extra_data = {}
        notify_channel = "email"
        for i in range(5):
            Events.add(**locals())

        event = Events.create_event(name, description, category)

        #get notifications
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event)), 5)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower2, event=event)), 5)
        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.actor, "event": event})

    def test_notification_with_subscription_no_active(self):
        name = "new_event_subs_no_active"
        category = "Blog"
        description = "New blog entry is created"
        object_type = "blog_post"
        object_id = "00"
        actor = self.actor
        extra_data = {}
        notify_channel = "email"
        event_params = locals()
        event = Events.create_event(name, description, category)

        Subscriptions.unfollow(follower=self.follower, event=event)

        Events.add(**event_params)

        #get notifications
        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.follower, "event": event})

        Notifications.objects.get(user=self.follower2, event=event)

        self.assertRaises(ObjectDoesNotExist,
                          callableObj=Notifications.objects.get,
                          *(), **{"user": self.actor, "event": event})

    def test_unfollow_category(self):

        event1_dict = {"name": "test_unfollow_category_1",
                       "category": "Blog_c",
                       "description": "New blog entry is created",
                       "object_type": "blog_post",
                       "object_id": "00",
                       "actor": self.actor,
                       "extra_data": {},
                       "notify_channel": "email",
        }

        event2_dict = {"name": "test_unfollow_category_2",
                       "category": "Blog_c",
                       "description": "New blog entry is created",
                       "object_type": "blog_post",
                       "object_id": "00",
                       "actor": self.actor,
                       "extra_data": {},
                       "notify_channel": "email"}

        event3_dict = {"name": "test_unfollow_category_3",
                       "category": "Blog_c2",
                       "description": "New blog entry is created",
                       "object_type": "blog_post",
                       "object_id": "00",
                       "actor": self.actor,
                       "extra_data": {},
                       "notify_channel": "email"}

        event1 = Events.create_event(event1_dict["name"], event1_dict["description"], event1_dict["category"])
        event2 = Events.create_event(event2_dict["name"], event2_dict["description"], event2_dict["category"])
        event3 = Events.create_event(event3_dict["name"], event3_dict["description"], event3_dict["category"])

        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        Subscriptions.unfollow(follower=self.follower, category=event2_dict["category"])

        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 2)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 2)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 0)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event1)), 1)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 0)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event2)), 1)

        Subscriptions.follow(follower=self.follower, category=event2_dict["category"])

        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 3)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 3)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 1)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event1)), 2)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 1)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event2)), 2)

    def test_unfollow_event(self):

        event1_dict = {"name": "test_unfollow_event_1",
                       "category": "Blog",
                       "description": "New blog entry is created",
                       "object_type": "blog_post",
                       "object_id": "00",
                       "actor": self.actor,
                       "extra_data": {},
                       "notify_channel": "email",
        }

        event2_dict = {"name": "test_unfollow_event_2",
                       "category": "Blog",
                       "description": "New blog entry is created",
                       "object_type": "blog_post",
                       "object_id": "00",
                       "actor": self.actor,
                       "extra_data": {},
                       "notify_channel": "email"}

        event3_dict = {"name": "test_unfollow_event_3",
                       "category": "Blog",
                       "description": "New blog entry is created",
                       "object_type": "blog_post",
                       "object_id": "00",
                       "actor": self.actor,
                       "extra_data": {},
                       "notify_channel": "email"}

        event1 = Events.create_event(event1_dict["name"], event1_dict["description"], event1_dict["category"])
        event2 = Events.create_event(event2_dict["name"], event2_dict["description"], event2_dict["category"])
        event3 = Events.create_event(event3_dict["name"], event3_dict["description"], event3_dict["category"])
        Subscriptions.objects.get(follower=self.follower, event=event3)
        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        Subscriptions.unfollow(follower=self.follower, event=event3)

        Events.add(**event3_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 0)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 1)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 1)

        Subscriptions.unfollow(follower=self.follower)
        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 0)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 1)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 0)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event1)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 0)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event2)), 1)

        Subscriptions.follow(follower=self.follower, event=event2)

        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 0)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 1)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 0)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event1)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 1)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event2)), 2)

        Subscriptions.follow(follower=self.follower)

        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 1)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 2)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 1)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event1)), 2)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 2)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event2)), 3)

    #follow and unfollow
    def test_unfollow_actor(self):

        event1_dict = {"name": "test_unfollow_actor_1",
                       "category": "Blog",
                       "description": "New blog entry is created",
                       "object_type": "blog_post",
                       "object_id": "00",
                       "actor": self.actor,
                       "extra_data": {},
                       "notify_channel": "email",
        }

        event2_dict = {"name": "test_unfollow_actor_2",
                       "category": "Blog",
                       "description": "New blog entry is created",
                       "object_type": "blog_post",
                       "object_id": "00",
                       "actor": self.actor,
                       "extra_data": {},
                       "notify_channel": "email"}

        event3_dict = {"name": "test_unfollow_actor_3",
                       "category": "Blog",
                       "description": "New blog entry is created",
                       "object_type": "blog_post",
                       "object_id": "00",
                       "actor": self.actor,
                       "extra_data": {},
                       "notify_channel": "email"}

        event1 = Events.create_event(event1_dict["name"], event1_dict["description"], event1_dict["category"])
        event2 = Events.create_event(event2_dict["name"], event2_dict["description"], event2_dict["category"])
        event3 = Events.create_event(event3_dict["name"], event3_dict["description"], event3_dict["category"])

        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        Subscriptions.unfollow(follower=self.follower, event=event3, actor=self.actor)

        Events.add(**event3_dict)

        event3_dict["actor"] = self.follower2
        Events.add(**event3_dict)


        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, actor=self.follower2, event=event3)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event3, actor=self.actor)), 0)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 2)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 1)

        Subscriptions.unfollow(follower=self.follower, actor=self.actor)

        Events.add(**event1_dict)
        Events.add(**event2_dict)
        event1_dict["actor"] = self.follower2
        event2_dict["actor"] = self.follower2
        Events.add(**event1_dict)
        Events.add(**event2_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, actor=self.follower2, event=event1)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, actor=self.follower2, event=event2)), 1)

        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event2)), 2)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event1)), 2)

        Subscriptions.follow(follower=self.follower, event=event3, actor=self.actor)

        event1_dict["actor"] = self.actor
        event2_dict["actor"] = self.actor
        event3_dict["actor"] = self.actor

        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 1)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event2)), 2)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event1)), 2)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 2)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 3)
        self.assertEqual(len(Notifications.get(user=self.follower, actor=self.follower2, event=event3)), 1)

        Subscriptions.follow(follower=self.follower, actor=self.actor)

        Events.add(**event1_dict)
        Events.add(**event2_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 2)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 2)
        self.assertEqual(len(Notifications.get(user=self.follower, actor=self.follower2, event=event1)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, actor=self.follower2, event=event2)), 1)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event2)), 3)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event1)), 3)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 2)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 3)
        self.assertEqual(len(Notifications.get(user=self.follower, actor=self.follower2, event=event3)), 1)

    #follow and unfollow
    def test_unfollow_object_type(self):

        event1_dict = {"name": "test_unfollow_object_type_1",
                       "category": "Blog",
                       "description": "New blog entry is created",
                       "object_type": "test_blog_post",
                       "object_id": "00",
                       "actor": self.actor,
                       "extra_data": {},
                       "notify_channel": "email",
        }

        event2_dict = {"name": "test_unfollow_object_type_2",
                       "category": "Blog",
                       "description": "New blog entry is created",
                       "object_type": "test_blog_post",
                       "object_id": "00",
                       "actor": self.actor,
                       "extra_data": {},
                       "notify_channel": "email"}

        event3_dict = {"name": "test_unfollow_object_type_3",
                       "category": "Blog",
                       "description": "New blog entry is created",
                       "object_type": "test_blog_post",
                       "object_id": "00",
                       "actor": self.actor,
                       "extra_data": {},
                       "notify_channel": "email"}

        event1 = Events.create_event(event1_dict["name"], event1_dict["description"], event1_dict["category"])
        event2 = Events.create_event(event2_dict["name"], event2_dict["description"], event2_dict["category"])
        event3 = Events.create_event(event3_dict["name"], event3_dict["description"], event3_dict["category"])

        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        Subscriptions.unfollow(follower=self.follower, event=event3, object_type=event3_dict["object_type"])

        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        event3_dict["object_type"] = "www"

        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, object_type="www", event=event3)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event3, object_type="test_blog_post")), 0)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 2)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 3)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 3)

        Subscriptions.unfollow(follower=self.follower, object_type = "test_blog_post")

        Events.add(**event1_dict)
        Events.add(**event2_dict)
        event1_dict["object_type"] = "www"
        event2_dict["object_type"] = "www"
        Events.add(**event1_dict)
        Events.add(**event2_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, object_type="www", event=event3)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event3, object_type="test_blog_post")), 0)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 2)


        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 1)

        Subscriptions.follow(follower=self.follower, object_type="test_blog_post", event = event3)

        event3_dict["object_type"] = "test_blog_post"
        event2_dict["object_type"] = "test_blog_post"
        event1_dict["object_type"] = "test_blog_post"
        Events.add(**event1_dict)
        Events.add(**event2_dict)
        Events.add(**event3_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 2)
        self.assertEqual(len(Notifications.get(user=self.follower, object_type="www", event=event3)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event3, object_type="test_blog_post")), 1)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 3)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 1)

        Subscriptions.follow(follower=self.follower, object_type="test_blog_post")

        Events.add(**event1_dict)
        Events.add(**event2_dict)

        self.assertEqual(len(Notifications.get(user=self.follower, event=event3)), 2)
        self.assertEqual(len(Notifications.get(user=self.follower, object_type="www", event=event3)), 1)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event3, object_type="test_blog_post")), 1)
        self.assertEqual(len(Notifications.objects.filter(user=self.follower, event=event3)), 3)


        self.assertEqual(len(Notifications.get(user=self.follower, event=event1)), 2)
        self.assertEqual(len(Notifications.get(user=self.follower, event=event2)), 2)