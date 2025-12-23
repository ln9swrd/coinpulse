"""
Surge Prediction History Admin API Routes
급등예측 이력 관리 API 엔드포인트 (관리자 전용)
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy import text
from backend.database.connection import get_db_session
from backend.middleware.auth import admin_required

surge_history_bp = Blueprint('surge_history', __name__, url_prefix='/api/admin/surge-history')


@surge_history_bp.route('', methods=['GET'])
@admin_required
def get_surge_history():
    """
    급등예측 이력 조회 (관리자 전용)

    Query Parameters:
    - page: 페이지 번호 (default: 1)
    - per_page: 페이지당 항목 수 (default: 50, max: 500)
    - market: 마켓 필터 (예: KRW-BTC)
    - signal_type: 신호 유형 필터 (예: surge)
    - auto_traded: 자동거래 여부 필터 (true/false)
    - status: 상태 필터 (예: active, closed)
    - start_date: 시작일 (YYYY-MM-DD)
    - end_date: 종료일 (YYYY-MM-DD)
    - sort: 정렬 기준 (sent_at, confidence, profit_loss)
    - order: 정렬 순서 (asc, desc)

    Returns:
        200: {
            "success": true,
            "data": [...],
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total": 100,
                "total_pages": 2
            },
            "stats": {
                "total_alerts": 100,
                "auto_traded_count": 50,
                "avg_confidence": 0.75,
                "total_profit_loss": 1000000,
                "profitable_trades": 30,
                "losing_trades": 20
            }
        }
    """
    try:
        # Parse query parameters
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(500, max(1, int(request.args.get('per_page', 50))))
        market = request.args.get('market')
        signal_type = request.args.get('signal_type')
        auto_traded = request.args.get('auto_traded')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort = request.args.get('sort', 'sent_at')
        order = request.args.get('order', 'desc').upper()

        # Validate sort and order
        valid_sorts = ['sent_at', 'confidence', 'profit_loss', 'expected_return']
        if sort not in valid_sorts:
            sort = 'sent_at'
        if order not in ['ASC', 'DESC']:
            order = 'DESC'

        with get_db_session() as session:
            # Build WHERE clauses
            where_clauses = []
            params = {}

            if market:
                where_clauses.append("market = :market")
                params['market'] = market

            if signal_type:
                where_clauses.append("signal_type = :signal_type")
                params['signal_type'] = signal_type

            if auto_traded is not None:
                where_clauses.append("auto_traded = :auto_traded")
                params['auto_traded'] = (auto_traded.lower() == 'true')

            if status:
                where_clauses.append("status = :status")
                params['status'] = status

            if start_date:
                where_clauses.append("sent_at >= :start_date")
                params['start_date'] = datetime.strptime(start_date, '%Y-%m-%d')

            if end_date:
                where_clauses.append("sent_at <= :end_date")
                params['end_date'] = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # Count total records
            count_query = f"SELECT COUNT(*) FROM surge_alerts{where_sql}"
            total = session.execute(text(count_query), params).scalar()

            # Calculate pagination
            total_pages = (total + per_page - 1) // per_page
            offset = (page - 1) * per_page

            # Get paginated data
            data_query = f"""
                SELECT
                    id, user_id, market, coin, confidence, signal_type,
                    current_price, target_price, expected_return,
                    reason, alert_message,
                    telegram_sent, telegram_message_id, sent_at,
                    week_number, user_action, action_timestamp,
                    entry_price, stop_loss_price,
                    auto_traded, trade_amount, trade_quantity, order_id,
                    status, profit_loss, profit_loss_percent,
                    executed_at, closed_at
                FROM surge_alerts
                {where_sql}
                ORDER BY {sort} {order}
                LIMIT :limit OFFSET :offset
            """

            params['limit'] = per_page
            params['offset'] = offset

            result = session.execute(text(data_query), params)
            alerts = []

            for row in result:
                alert = dict(row._mapping)
                # Convert datetime to ISO string
                for key in ['sent_at', 'action_timestamp', 'executed_at', 'closed_at']:
                    if alert.get(key):
                        alert[key] = alert[key].isoformat()
                alerts.append(alert)

            # Get statistics
            stats_query = f"""
                SELECT
                    COUNT(*) as total_alerts,
                    SUM(CASE WHEN auto_traded = true THEN 1 ELSE 0 END) as auto_traded_count,
                    AVG(confidence) as avg_confidence,
                    SUM(COALESCE(profit_loss, 0)) as total_profit_loss,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as profitable_trades,
                    SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades
                FROM surge_alerts
                {where_sql}
            """

            stats_result = session.execute(text(stats_query), params).fetchone()
            stats = {
                'total_alerts': stats_result[0] or 0,
                'auto_traded_count': stats_result[1] or 0,
                'avg_confidence': round(float(stats_result[2] or 0), 4),
                'total_profit_loss': int(stats_result[3] or 0),
                'profitable_trades': stats_result[4] or 0,
                'losing_trades': stats_result[5] or 0
            }

            return jsonify({
                'success': True,
                'data': alerts,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages
                },
                'stats': stats
            }), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid parameter: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@surge_history_bp.route('/<int:alert_id>', methods=['GET'])
@admin_required
def get_surge_alert_detail(alert_id):
    """
    급등예측 단일 항목 상세 조회

    Returns:
        200: Alert detail with user information
        404: Alert not found
    """
    try:
        with get_db_session() as session:
            query = text("""
                SELECT
                    sa.*,
                    u.username, u.email
                FROM surge_alerts sa
                LEFT JOIN users u ON sa.user_id = u.id
                WHERE sa.id = :alert_id
            """)

            result = session.execute(query, {'alert_id': alert_id}).fetchone()

            if not result:
                return jsonify({
                    'success': False,
                    'error': 'Alert not found'
                }), 404

            alert = dict(result._mapping)

            # Convert datetime to ISO string
            for key in ['sent_at', 'action_timestamp', 'executed_at', 'closed_at']:
                if alert.get(key):
                    alert[key] = alert[key].isoformat()

            return jsonify({
                'success': True,
                'data': alert
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@surge_history_bp.route('/markets', methods=['GET'])
@admin_required
def get_available_markets():
    """
    급등예측에 사용된 마켓 목록 조회

    Returns:
        200: List of markets with count
    """
    try:
        with get_db_session() as session:
            query = text("""
                SELECT market, COUNT(*) as count
                FROM surge_alerts
                GROUP BY market
                ORDER BY count DESC
            """)

            result = session.execute(query)
            markets = [{'market': row[0], 'count': row[1]} for row in result]

            return jsonify({
                'success': True,
                'markets': markets
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@surge_history_bp.route('/export', methods=['GET'])
@admin_required
def export_surge_history():
    """
    급등예측 이력 CSV 내보내기

    Query Parameters: Same as get_surge_history

    Returns:
        200: CSV file
    """
    try:
        # Same filters as get_surge_history
        market = request.args.get('market')
        signal_type = request.args.get('signal_type')
        auto_traded = request.args.get('auto_traded')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        with get_db_session() as session:
            # Build WHERE clauses
            where_clauses = []
            params = {}

            if market:
                where_clauses.append("market = :market")
                params['market'] = market

            if signal_type:
                where_clauses.append("signal_type = :signal_type")
                params['signal_type'] = signal_type

            if auto_traded is not None:
                where_clauses.append("auto_traded = :auto_traded")
                params['auto_traded'] = (auto_traded.lower() == 'true')

            if status:
                where_clauses.append("status = :status")
                params['status'] = status

            if start_date:
                where_clauses.append("sent_at >= :start_date")
                params['start_date'] = datetime.strptime(start_date, '%Y-%m-%d')

            if end_date:
                where_clauses.append("sent_at <= :end_date")
                params['end_date'] = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # Get all data (no pagination for export)
            query = f"""
                SELECT
                    id, user_id, market, coin, confidence, signal_type,
                    current_price, target_price, expected_return,
                    telegram_sent, sent_at,
                    auto_traded, trade_amount, order_id,
                    status, profit_loss, profit_loss_percent,
                    executed_at, closed_at
                FROM surge_alerts
                {where_sql}
                ORDER BY sent_at DESC
            """

            result = session.execute(text(query), params)

            # Build CSV
            import io
            output = io.StringIO()
            output.write('ID,User ID,Market,Coin,Confidence,Signal Type,Current Price,Target Price,Expected Return,Telegram Sent,Sent At,Auto Traded,Trade Amount,Order ID,Status,Profit Loss,Profit Loss %,Executed At,Closed At\n')

            for row in result:
                row_dict = dict(row._mapping)
                output.write(','.join([
                    str(row_dict.get('id', '')),
                    str(row_dict.get('user_id', '')),
                    str(row_dict.get('market', '')),
                    str(row_dict.get('coin', '')),
                    str(row_dict.get('confidence', '')),
                    str(row_dict.get('signal_type', '')),
                    str(row_dict.get('current_price', '')),
                    str(row_dict.get('target_price', '')),
                    str(row_dict.get('expected_return', '')),
                    str(row_dict.get('telegram_sent', '')),
                    str(row_dict.get('sent_at', '')),
                    str(row_dict.get('auto_traded', '')),
                    str(row_dict.get('trade_amount', '')),
                    str(row_dict.get('order_id', '')),
                    str(row_dict.get('status', '')),
                    str(row_dict.get('profit_loss', '')),
                    str(row_dict.get('profit_loss_percent', '')),
                    str(row_dict.get('executed_at', '')),
                    str(row_dict.get('closed_at', ''))
                ]) + '\n')

            # Return CSV
            from flask import make_response
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
            response.headers['Content-Disposition'] = f'attachment; filename=surge_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            return response

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
