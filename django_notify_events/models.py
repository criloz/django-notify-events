from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Min
import time
import json


class Events(models.Model):
    """
        store the type of events
    """

    #name of the event
    name = models.CharField(max_length=60, null=False, blank=False)

    #description of the event
    description = models.TextField()

    #event category
    category = models.CharField(max_length=60, null=False, blank=False)

    active = models.BooleanField(default=True)

    auto_subscription = models.BooleanField(default=True)

    @classmethod
    def do_filter(cls, filter=None, *args, **kwargs):
        if filter is not None:
            ret = filter(*args, **kwargs)
            if isinstance(ret, bool):
                return ret
            else:
                raise TypeError("filter must return a bool")
        return True

    @classmethod
    def deactivate_category(cls, category):
        for event in cls.objects.filter(category=category):
            event.active = False
            event.save()

    @classmethod
    def activate_category(cls, category):
        for event in cls.objects.filter(category=category):
            event.active = True
            event.save()

    @classmethod
    def create_event(cls, name, description, category, auto_subscription=True):
        try:
            event = cls.objects.get(name=name)
        except ObjectDoesNotExist:
            event = cls.objects.create(name=name,
                                       description=description,
                                       category=category,
                                       auto_subscription=auto_subscription)

            if auto_subscription:
                #create default subscriptions
                users = User.objects.all()

                #get all events of the category
                events_of_this_category = cls.objects.filter(category=category)

                for user in users:
                    #get min period register for this category
                    min_period = Subscriptions.objects.filter(follower=user,
                                                              event__in=events_of_this_category).aggregate(Min('period'))

                    min_period = 0 if min_period["period__min"] is None else min_period["period__min"]
                    Subscriptions.objects.create(follower=user,
                                                 event=event,
                                                 period=min_period)

        return event

    @classmethod
    def add(cls, **kwargs):
        kwargs.setdefault("extra_data", {})
        kwargs.setdefault("notify_channel", None)
        kwargs.setdefault("filter", None)
        kwargs.setdefault("auto_subscription", True)
        filter = kwargs.pop("filter")
        try:
            #get event if exist
            event = cls.create_event(kwargs["name"],
                                     kwargs["description"],
                                     kwargs["category"],
                                     kwargs["auto_subscription"])

            if event.active:
                #create notifications

                #get generals active subs of the event
                for sub in Subscriptions.get(event=event):

                    if sub.follower == kwargs["actor"]:
                        continue

                    if not sub.active:
                        continue

                    if kwargs["actor"].username in sub.unfollow_actors.split(","):
                        continue

                    if not cls.do_filter(filter, subscription=sub, **kwargs):
                        continue

                    rules = json.loads(sub.rules)

                    if kwargs["object_type"] in rules[0]:
                        continue

                    if [kwargs["object_type"], kwargs["actor"].username] in rules[1]:
                        continue

                    if [kwargs["object_type"], kwargs["object_id"]] in rules[2]:
                        continue

                    if [kwargs["object_type"], kwargs["object_id"], kwargs["actor"].username] in rules[3]:
                        continue

                    Notifications.objects.create(user=sub.follower,
                                                 event=event,
                                                 actor=kwargs["actor"],
                                                 object_type=kwargs["object_type"],
                                                 object_id=kwargs["object_id"],
                                                 extra_data=json.dumps(kwargs["extra_data"]),
                                                 notify_channel=kwargs["notify_channel"],
                                                 dispatch_time=int(time.time())+sub.period)
                return event

        except KeyError as e:
            raise TypeError("The argument %s is missing" % e.message)


class Subscriptions(models.Model):
    """
        store subscriptions
    """

    #user following the event
    follower = models.ForeignKey(User, related_name='follower_user')
    #event name
    event = models.ForeignKey(Events)
    #user that generate the event (all, for all users)
    unfollow_actors = models.TextField(blank=True, null=False, default="")
    #rules for filter notifications
    #1 only by object type
    # object type object id
    # object type, object id, actor
    rules = models.TextField(blank=False, null=False, default="[[],[],[],[]]")
    #the minimum time for django_notify_events to the user this event
    period = models.BigIntegerField(default=0)
    #the notification channel of this event
    notify_channels = models.TextField(null=True, blank=False)
    active = models.BooleanField(default=True)

    @classmethod
    def get(cls, *args, **kwargs):
        return cls.objects.filter(active=True, *args, **kwargs)

    @classmethod
    def follow(cls, **kwargs):
        actor = kwargs.get("actor", None)
        event = kwargs.get("event", None)
        object_type = kwargs.get("object_type", None)
        object_id = kwargs.get("object_id", None)
        follower = kwargs["follower"]
        category = kwargs.get("category", None)

        if actor is not None and object_type is None and object_id is None and category is None:
            if event is None:
                for sub in Subscriptions.objects.filter(follower=follower):
                    unfollow_actors = set(sub.unfollow_actors.split(","))
                    if actor.username in unfollow_actors:
                        unfollow_actors.remove(actor.username)

                    sub.unfollow_actors = ",".join(unfollow_actors)
                    sub.save()
            else:
                sub = Subscriptions.objects.get(follower=follower, event=event)
                unfollow_actors = set(sub.unfollow_actors.split(","))
                if actor.username in unfollow_actors:
                    unfollow_actors.remove(actor.username)

                sub.unfollow_actors = ",".join(unfollow_actors)
                sub.save()

        elif actor is None and object_type is not None and object_id is None and category is None:
            if event is None:
                for sub in Subscriptions.objects.filter(follower=follower):
                    rules = json.loads(sub.rules)
                    rules[0] = set(rules[0])
                    if object_type in rules[0]:
                        rules[0].remove(object_type)
                    rules[0] = list(rules[0])
                    sub.rules = json.dumps(rules)
                    sub.save()

            else:
                sub = Subscriptions.objects.get(follower=follower, event=event)
                rules = json.loads(sub.rules)
                rules[0] = set(rules[0])

                if object_type in rules[0]:
                    rules[0].remove(object_type)

                rules[0] = list(rules[0])
                sub.rules = json.dumps(rules)
                sub.save()

        elif actor is None and object_type is None and object_id is None and category is None:
            if event is None:
                cls.objects.filter(follower=follower).update(active=True)
            else:
                cls.objects.filter(follower=follower, event=event).update(active=True)
        elif actor is None and object_type is None and object_id is None and category is not None and event is None:
            events = Events.objects.filter(category=category)
            cls.objects.filter(follower=follower, event__in=events).update(active=True)
        else:
            raise TypeError("Bad Arguments")

    @classmethod
    def unfollow(cls, **kwargs):
        actor = kwargs.get("actor", None)
        event = kwargs.get("event", None)
        object_type = kwargs.get("object_type", None)
        object_id = kwargs.get("object_id", None)
        category = kwargs.get("category", None)
        follower = kwargs["follower"]

        if actor is not None and object_type is None and object_id is None and category is None:
            if event is None:
                for sub in Subscriptions.objects.filter(follower=follower):
                    unfollow_actors = sub.unfollow_actors.split(",")
                    unfollow_actors.append(actor.username)
                    sub.unfollow_actors = ",".join(set(unfollow_actors))
                    sub.save()
                    Notifications.get(user=follower, actor=actor).update(read=True)
            else:
                sub = Subscriptions.objects.get(follower=follower, event=event)
                unfollow_actors = sub.unfollow_actors.split(",")
                unfollow_actors.append(actor.username)
                sub.unfollow_actors = ",".join(set(unfollow_actors))
                sub.save()
                Notifications.get(user=follower, event=event, actor=actor).update(read=True)

        elif actor is None and object_type is not None and object_id is None and category is None:
            if event is None:
                for sub in Subscriptions.objects.filter(follower=follower):
                    rules = json.loads(sub.rules)
                    rules[0] = set(rules[0])
                    rules[0].add(object_type)
                    rules[0] = list(rules[0])
                    sub.rules = json.dumps(rules)
                    sub.save()
                Notifications.get(user=follower, object_type=object_type).update(read=True)

            else:
                sub = Subscriptions.objects.get(follower=follower, event=event)
                rules = json.loads(sub.rules)
                rules[0] = set(rules[0])
                rules[0].add(object_type)
                rules[0] = list(rules[0])
                sub.rules = json.dumps(rules)
                sub.save()
                Notifications.get(user=follower, event=event, object_type=object_type).update(read=True)

        elif actor is None and object_type is None and object_id is None and category is None:
            if event is None:
                cls.objects.filter(follower=follower).update(active=False)
                Notifications.get(user=follower).update(read=True)
            else:
                cls.objects.filter(follower=follower, event=event).update(active=False)
                Notifications.get(user=follower, event=event).update(read=True)

        elif actor is None and object_type is None and object_id is None and category is not None and event is None:
            events = Events.objects.filter(category=category)
            cls.objects.filter(follower=follower, event__in=events).update(active=False)
            Notifications.get(user=follower, event__in=events).update(read=True)

        else:
            raise TypeError("Bad Arguments")


class Notifications(models.Model):
    """
        store all the notifications
    """

    user = models.ForeignKey(User, related_name='follower_notification')
    event = models.ForeignKey(Events)
    actor = models.ForeignKey(User,  related_name='actor_notification')
    object_type = models.CharField(max_length=20, null=False, blank=False)
    object_id = models.CharField(max_length=20, null=False, blank=False)
    extra_data = models.TextField(default='{}')
    notify_channel = models.CharField(max_length=20, null=True)
    read = models.BooleanField(default=False)
    dispatch_time = models.BigIntegerField(default=0)

    @classmethod
    def get(cls, *args, **kwargs):
        return cls.objects.filter(read=False, dispatch_time__lte=int(time.time()), *args, **kwargs)