from datetime import timedelta
from uuid import uuid4

import pytest
import requests_mock

import tosspay
from tosspay.entity import Payment
from tosspay.response import APIError, PurchaseResult, ApprovedResult


def test_purchase():
    c = tosspay.TossPayClient(development=True)
    order_id = str(uuid4())

    with pytest.raises(ValueError):
        c.purchase(order_id + '&', 40000, 'test', '', True)

    with pytest.raises(ValueError):
        c.purchase(order_id, 40000, 'test', '', True,
                   expired_time=timedelta(hours=1, minutes=1))

    with pytest.raises(tosspay.exc.NotAutoExecutable):
        c.purchase(order_id, 40000, 'test', '', True,
                   auto_execute=True)

    result = c.purchase(order_id, 40000, 'test', '', True)

    assert result.pay_token is not None
    assert result.purchase_url is not None

    order_id = str(uuid4())
    result = c.purchase(order_id, 40000, 'test', '', True,
                        auto_execute=True, result_callback='test')

    assert result.pay_token is not None
    assert result.purchase_url is not None
    assert isinstance(result, PurchaseResult)

    result = c.purchase(order_id, 0, 'test', '', True,
                        auto_execute=True, result_callback='test')
    assert isinstance(result, APIError)
    assert result.data["status"] == 200
    assert result.data["code"] == -1
    assert result.msg == '요청한 값이 부족하거나 올바르지 않습니다. amount는 0보다 커야 합니다.'
    assert result.data["errorCode"] == 'COMMON_INVALID_PARAMETER'


def test_get_payment():
    pay_token = "N4GOTJB5eR3Tnx8kJeVp90"

    c = tosspay.TossPayClient(development=True)
    result = c.get_payment(pay_token)

    assert isinstance(result, Payment)


def test_purchase_result():

    c = tosspay.TossPayClient(development=True)
    order_id = str(uuid4())

    purchase_result = c.purchase(order_id, 40000, 'test', '', True)

    payment = purchase_result.payment

    assert isinstance(payment, Payment)
    assert payment.amount == 40000
    assert payment.product_desc == 'test'
    assert payment.pay_status == 'PAY_STANDBY'


def test_confirm_purchase():

    c = tosspay.TossPayClient(development=True)
    order_id = str(uuid4())
    purchase_result = c.purchase(order_id, 40000, 'test', '', True)
    payment = purchase_result.payment

    approved_result = c.approve(payment.pay_token)

    assert isinstance(approved_result, APIError)
    assert approved_result.msg == '사용자 정보가 존재하지 않습니다.'

    result = c.purchase(order_id, 40000, 'test', '', True)
    token = result.payment.pay_token

    with requests_mock.Mocker() as m:
        # NOTE: toss user-side auth 가 자동화될 수가 없어 mocking 으로 우회
        m.post('https://pay.toss.im/api/v1/execute',
               text='{"code":0,"approvalTime":"2016-11-16 13:59:59"}')
        approved_result = c.approve(token)

    assert isinstance(approved_result, ApprovedResult)

