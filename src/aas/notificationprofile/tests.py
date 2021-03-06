from datetime import datetime, time

from django.test import TransactionTestCase
from django.utils import timezone
from django.utils.timezone import make_aware
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITransactionTestCase

from aas.alert.models import Alert, NetworkSystem, Object, ObjectType, ProblemType
from aas.alert.serializers import AlertSerializer
from aas.auth.models import User
from aas.notificationprofile.models import (
    Filter,
    NotificationProfile,
    TimeInterval,
    TimeSlot,
)


class MockAlertData:
    # Define member variables, to avoid warnings
    user = None
    nav1 = None
    zabbix1 = None
    object_type1 = None
    object1 = None
    problem_type1 = None
    alert1 = None
    alert2 = None

    def init_mock_data(self):
        self.user = User.objects.create(username="asdf")

        self.nav1 = NetworkSystem.objects.create(
            name="Gløshaugen", type=NetworkSystem.NAV
        )
        self.zabbix1 = NetworkSystem.objects.create(
            name="Gløshaugen", type=NetworkSystem.ZABBIX
        )

        self.object_type1 = ObjectType.objects.create(name="box")
        self.object1 = Object.objects.create(name="1", url="", type=self.object_type1)

        self.problem_type1 = ProblemType.objects.create(
            name="boxDown", description="A box is down."
        )

        self.alert1 = Alert.objects.create(
            timestamp=timezone.now(),
            source=self.nav1,
            alert_id="123",
            object=self.object1,
            problem_type=self.problem_type1,
        )
        self.alert2 = Alert.objects.get(pk=self.alert1.pk)
        self.alert2.pk = None  # clones alert1
        self.alert2.source = self.zabbix1
        self.alert2.save()


class TestModels(TransactionTestCase, MockAlertData):
    @staticmethod
    def replace_time(timestamp: datetime, new_time: str):
        new_time = time.fromisoformat(new_time)
        return timestamp.replace(
            hour=new_time.hour,
            minute=new_time.minute,
            second=new_time.second,
            microsecond=new_time.microsecond,
        )

    def setUp(self):
        super().init_mock_data()
        self.monday_time = make_aware(datetime.fromisoformat("2019-11-25"))

        self.time_slot1 = TimeSlot.objects.create(user=self.user, name="Test")
        self.interval1 = TimeInterval.objects.create(
            time_slot=self.time_slot1,
            day=TimeInterval.MONDAY,
            start=time.fromisoformat("00:30:00"),
            end=time.fromisoformat("00:30:01"),
        )
        self.interval2 = TimeInterval.objects.create(
            time_slot=self.time_slot1,
            day=TimeInterval.MONDAY,
            start=time.fromisoformat("00:30:03"),
            end=time.fromisoformat("00:31"),
        )
        self.interval_all_day = TimeInterval.objects.create(
            time_slot=self.time_slot1,
            day=TimeInterval.TUESDAY,
            start=TimeInterval.DAY_START,
            end=TimeInterval.DAY_END,
        )

    def test_time_interval(self):
        # Test replace_time() helper function
        self.assertEqual(
            datetime.fromisoformat("2000-01-01 10:00"),
            self.replace_time(datetime.fromisoformat("2000-01-01"), "10:00"),
        )

        self.assertEqual(TimeInterval.DAY_NAME_TO_INDEX["MO"], 1)
        self.assertEqual(self.monday_time.strftime("%A"), "Monday")

        self.assertFalse(
            self.interval1.timestamp_is_within(
                self.replace_time(self.monday_time, "00:29:01")
            )
        )
        self.assertTrue(
            self.interval1.timestamp_is_within(
                self.replace_time(self.monday_time, "00:30:00")
            )
        )
        self.assertTrue(
            self.interval1.timestamp_is_within(
                self.replace_time(self.monday_time, "00:30:01")
            )
        )
        self.assertFalse(
            self.interval1.timestamp_is_within(
                self.replace_time(self.monday_time, "00:30:02")
            )
        )

    def test_time_slot(self):
        self.assertTrue(
            self.time_slot1.timestamp_is_within_time_intervals(
                self.replace_time(self.monday_time, "00:30:01")
            )
        )
        self.assertFalse(
            self.time_slot1.timestamp_is_within_time_intervals(
                self.replace_time(self.monday_time, "00:30:02")
            )
        )
        self.assertTrue(
            self.time_slot1.timestamp_is_within_time_intervals(
                self.replace_time(self.monday_time, "00:30:03")
            )
        )

    def test_filter(self):
        filter1 = Filter.objects.create(
            user=self.user,
            name="Filter1",
            filter_string="{"
            f'"sourceIds":[{self.nav1.pk}], "objectTypeIds":[], "parentObjectIds":[], "problemTypeIds":[]'
            "}",
        )
        filter2 = Filter.objects.create(
            user=self.user,
            name="Filter2",
            filter_string="{"
            f'"sourceIds":[{self.zabbix1.pk}], "objectTypeIds":[], "parentObjectIds":[], "problemTypeIds":[]'
            "}",
        )

        self.assertTrue(filter1.alert_fits(self.alert1))
        self.assertFalse(filter1.alert_fits(self.alert2))

        self.assertFalse(filter2.alert_fits(self.alert1))
        self.assertTrue(filter2.alert_fits(self.alert2))

        self.assertEqual(set(filter1.filtered_alerts), {self.alert1})
        self.assertEqual(set(filter2.filtered_alerts), {self.alert2})


class TestViews(APITransactionTestCase, MockAlertData):
    def setUp(self):
        super().init_mock_data()

        user_token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + user_token.key)

        alert1_json = AlertSerializer([self.alert1], many=True).data
        self.alert1_json = JSONRenderer().render(alert1_json)

        time_slot1 = TimeSlot.objects.create(user=self.user, name="Never")
        filter1 = Filter.objects.create(
            user=self.user,
            name="Critical alerts",
            filter_string="{"
            f'"sourceIds":[{self.nav1.pk}], "objectTypeIds":[], "parentObjectIds":[], "problemTypeIds":[]'
            "}",
        )
        self.notification_profile1 = NotificationProfile.objects.create(
            user=self.user, time_slot=time_slot1
        )
        self.notification_profile1.filters.add(filter1)

    def test_alerts_filtered_by_notification_profile_view(self):
        response = self.client.get(
            f"/notificationprofiles/{self.notification_profile1.pk}/alerts/"
        )
        response.render()
        self.assertEqual(response.content, self.alert1_json)

    # TODO: test more endpoints
