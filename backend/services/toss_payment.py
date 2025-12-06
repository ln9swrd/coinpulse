"""
CoinPulse - Toss Payments Integration Service
토스페이먼츠 API 연동 서비스

API Documentation: https://docs.tosspayments.com/
"""

import os
import requests
import base64
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TossPaymentService:
    """
    토스페이먼츠 API 연동 클래스
    
    주요 기능:
    - 일반 결제 (카드, 간편결제)
    - 정기 결제 (빌링키 발급 및 자동 결제)
    - 결제 승인/취소
    - 웹훅 처리
    """
    
    def __init__(self):
        """Initialize Toss Payments Service"""
        # API 키 로드
        self.secret_key = os.getenv('TOSS_SECRET_KEY')
        self.client_key = os.getenv('TOSS_CLIENT_KEY')
        
        # API 엔드포인트
        self.base_url = 'https://api.tosspayments.com'
        
        # 인증 헤더 생성
        if self.secret_key:
            credentials = f"{self.secret_key}:"
            encoded = base64.b64encode(credentials.encode()).decode()
            self.headers = {
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/json'
            }
        else:
            logger.warning("TOSS_SECRET_KEY not found in environment")
            self.headers = {}
    
    def create_payment(
        self,
        amount: int,
        order_id: str,
        order_name: str,
        customer_email: str,
        customer_name: str,
        success_url: str,
        fail_url: str
    ) -> Dict:
        """
        일반 결제 요청 생성
        
        Args:
            amount: 결제 금액 (원)
            order_id: 주문 ID (고유값)
            order_name: 주문명
            customer_email: 고객 이메일
            customer_name: 고객명
            success_url: 결제 성공 리다이렉트 URL
            fail_url: 결제 실패 리다이렉트 URL
            
        Returns:
            Dict: 결제 요청 데이터 (프론트엔드에서 사용)
        """
        payment_data = {
            'amount': amount,
            'orderId': order_id,
            'orderName': order_name,
            'customerEmail': customer_email,
            'customerName': customer_name,
            'successUrl': success_url,
            'failUrl': fail_url
        }
        
        logger.info(f"[TossPayment] Payment created: {order_id}, {amount}원")
        return payment_data
    
    def confirm_payment(
        self,
        payment_key: str,
        order_id: str,
        amount: int
    ) -> Dict:
        """
        결제 승인
        
        Args:
            payment_key: 토스페이먼츠 결제 키
            order_id: 주문 ID
            amount: 결제 금액
            
        Returns:
            Dict: 결제 승인 결과
        """
        url = f"{self.base_url}/v1/payments/confirm"
        
        data = {
            'paymentKey': payment_key,
            'orderId': order_id,
            'amount': amount
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[TossPayment] Payment confirmed: {order_id}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[TossPayment] Payment confirmation failed: {str(e)}")
            raise
    
    def cancel_payment(
        self,
        payment_key: str,
        cancel_reason: str
    ) -> Dict:
        """
        결제 취소
        
        Args:
            payment_key: 토스페이먼츠 결제 키
            cancel_reason: 취소 사유
            
        Returns:
            Dict: 취소 결과
        """
        url = f"{self.base_url}/v1/payments/{payment_key}/cancel"
        
        data = {
            'cancelReason': cancel_reason
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[TossPayment] Payment cancelled: {payment_key}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[TossPayment] Payment cancellation failed: {str(e)}")
            raise
    
    def issue_billing_key(
        self,
        customer_key: str,
        auth_key: str
    ) -> Dict:
        """
        빌링키 발급 (정기 결제용)
        
        Args:
            customer_key: 고객 고유 키 (user_id 등)
            auth_key: 인증 키 (카드 등록 시 받은 키)
            
        Returns:
            Dict: 빌링키 정보
        """
        url = f"{self.base_url}/v1/billing/authorizations/issue"
        
        data = {
            'customerKey': customer_key,
            'authKey': auth_key
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[TossPayment] Billing key issued: {customer_key}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[TossPayment] Billing key issue failed: {str(e)}")
            raise
    
    def charge_billing(
        self,
        billing_key: str,
        customer_key: str,
        amount: int,
        order_id: str,
        order_name: str,
        customer_email: str
    ) -> Dict:
        """
        빌링키로 자동 결제 실행
        
        Args:
            billing_key: 발급받은 빌링키
            customer_key: 고객 고유 키
            amount: 결제 금액
            order_id: 주문 ID
            order_name: 주문명
            customer_email: 고객 이메일
            
        Returns:
            Dict: 결제 결과
        """
        url = f"{self.base_url}/v1/billing/{billing_key}"
        
        data = {
            'customerKey': customer_key,
            'amount': amount,
            'orderId': order_id,
            'orderName': order_name,
            'customerEmail': customer_email
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[TossPayment] Billing charged: {order_id}, {amount}원")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[TossPayment] Billing charge failed: {str(e)}")
            raise
    
    def get_payment(self, payment_key: str) -> Dict:
        """
        결제 정보 조회
        
        Args:
            payment_key: 토스페이먼츠 결제 키
            
        Returns:
            Dict: 결제 정보
        """
        url = f"{self.base_url}/v1/payments/{payment_key}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[TossPayment] Get payment failed: {str(e)}")
            raise


# Singleton instance
_toss_service = None

def get_toss_payment_service() -> TossPaymentService:
    """Get or create TossPaymentService singleton"""
    global _toss_service
    if _toss_service is None:
        _toss_service = TossPaymentService()
    return _toss_service
