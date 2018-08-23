import datetime
import pytest
from django.test import TestCase
from koalixcrm.crm.factories.factory_user import AdminUserFactory
from koalixcrm.crm.factories.factory_customer_billing_cycle import StandardCustomerBillingCycleFactory
from koalixcrm.crm.factories.factory_customer import StandardCustomerFactory
from koalixcrm.crm.factories.factory_customer_group import StandardCustomerGroupFactory
from koalixcrm.crm.factories.factory_currency import StandardCurrencyFactory
from koalixcrm.crm.factories.factory_reporting_period import StandardReportingPeriodFactory
from koalixcrm.djangoUserExtension.factories.factory_user_extension import StandardUserExtensionFactory
from koalixcrm.crm.factories.factory_task_status import DoneTaskStatusFactory
from koalixcrm.crm.factories.factory_task import StandardTaskFactory
from koalixcrm.global_support_functions import get_today_date


@pytest.fixture()
def freeze(monkeypatch):
    """ Now() manager patches date return a fixed, settable, value
        (freezes date)
    """
    import datetime
    original = datetime.date

    class FreezeMeta(type):
        def __instancecheck__(self, instance):
            if type(instance) == original or type(instance) == Freeze:
                return True

    class Freeze(datetime.datetime):
        __metaclass__ = FreezeMeta

        @classmethod
        def freeze(cls, val):
            cls.frozen = val

        @classmethod
        def date(cls):
            return cls.frozen

        @classmethod
        def delta(cls, timedelta=None, **kwargs):
            """ Moves time fwd/bwd by the delta"""
            from datetime import timedelta as td
            if not timedelta:
                timedelta = td(**kwargs)
            cls.frozen += timedelta

    monkeypatch.setattr(datetime, 'date', Freeze)
    Freeze.freeze(original.today())
    return Freeze


class TaskUpdateLastStatusUpdate(TestCase):

    @pytest.fixture(autouse=True)
    def freeze_time(self, freeze):
        self._freeze = freeze

    def setUp(self):
        datetime_now = datetime.datetime(2024, 1, 1, 0, 00)
        start_date = (datetime_now - datetime.timedelta(days=30)).date().__str__()
        end_date_first_task = (datetime_now + datetime.timedelta(days=30)).date().__str__()
        end_date_second_task = (datetime_now + datetime.timedelta(days=60)).date().__str__()

        self.test_billing_cycle = StandardCustomerBillingCycleFactory.create()
        self.test_user = AdminUserFactory.create()
        self.test_customer_group = StandardCustomerGroupFactory.create()
        self.test_customer = StandardCustomerFactory.create(is_member_of=(self.test_customer_group,))
        self.test_currency = StandardCurrencyFactory.create()
        self.test_user_extension = StandardUserExtensionFactory.create(user=self.test_user)
        self.test_reporting_period = StandardReportingPeriodFactory.create()
        self.test_1st_task = StandardTaskFactory.create(title="1st Test Task",
                                                        planned_start_date=start_date,
                                                        planned_end_date=end_date_first_task,
                                                        project=self.test_reporting_period.project,
                                                        last_status_change='2018-06-15'
                                                        )
        self.test_2nd_task = StandardTaskFactory.create(title="2nd Test Task",
                                                        planned_start_date=start_date,
                                                        planned_end_date=end_date_second_task,
                                                        project=self.test_reporting_period.project,
                                                        last_status_change='2018-06-15')

    def test_last_status_update(self):
        previous_last_status_change = self.test_1st_task.last_status_change
        new_status = DoneTaskStatusFactory.create()
        self._freeze.freeze(datetime.date(2024, 6, 2))
        print(get_today_date())
        print(datetime.date.today())
        self.test_1st_task.status = new_status
        self.test_1st_task.save()
        self.assertEquals(previous_last_status_change, '2018-06-15')
        self.assertEqual(self.test_1st_task.last_status_change, datetime.date(2024, 6, 2))