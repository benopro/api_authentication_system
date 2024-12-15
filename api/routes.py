from flask import Blueprint, request, jsonify
from .auth import jwt_required
from .models import db, User, CodeSession
from .code_assistant import CodeAssistant
import logging
from datetime import datetime

# Thiết lập logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

api = Blueprint('api', __name__)
code_assistant = CodeAssistant()

@api.route('/code-assist', methods=['POST'])
@jwt_required
def code_assistance():
    """
    Endpoint để xử lý yêu cầu hỗ trợ code
    """
    try:
        # Lấy dữ liệu từ request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate và lấy các trường dữ liệu
        query = data.get('query')
        code_context = data.get('code_context', '')
        language = data.get('language', 'python')
        
        # Kiểm tra query bắt buộc
        if not query:
            return jsonify({'error': 'Query is required'}), 400
            
        logger.debug(f"Processing code assist request: {query[:100]}...")
        
        # Gọi code assistant để xử lý
        response = code_assistant.process_request(
            query=query,
            code_context=code_context,
            language=language
        )
        
        if not response.get('success'):
            return jsonify({
                'error': 'Code assistant processing failed',
                'details': response.get('error')
            }), 500

        # Lưu session vào database
        try:
            session = CodeSession(
                user_id=request.user_id,
                query=query,
                code_context=code_context,
                response=response['response'],
                language=language,
                tokens_used=response.get('tokens_used', 0),
                created_at=datetime.utcnow()
            )
            db.session.add(session)
            db.session.commit()
            logger.debug(f"Saved code session for user {request.user_id}")
            
        except Exception as e:
            logger.error(f"Error saving code session: {str(e)}")
            db.session.rollback()
            # Vẫn trả về response nhưng log lỗi lưu session
            
        return jsonify({
            'success': True,
            'response': response['response'],
            'tokens_used': response.get('tokens_used', 0),
            'session_id': session.id if session else None
        })
        
    except Exception as e:
        logger.error(f"Code assist error: {str(e)}")
        return jsonify({
            'error': 'Code assist failed',
            'details': str(e)
        }), 500

@api.route('/history', methods=['GET'])
@jwt_required
def get_history():
    """
    Endpoint để lấy lịch sử code sessions của user
    """
    try:
        logger.debug(f"Getting history for user_id: {request.user_id}")
        
        # Truy vấn database
        sessions = db.session.query(CodeSession)\
            .filter(CodeSession.user_id == request.user_id)\
            .order_by(CodeSession.created_at.desc())\
            .all()
            
        # Format response
        history = [{
            'id': session.id,
            'query': session.query,
            'code_context': session.code_context,
            'response': session.response,
            'language': session.language,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'tokens_used': session.tokens_used
        } for session in sessions]
        
        logger.debug(f"Found {len(history)} sessions for user {request.user_id}")
        
        return jsonify({
            'success': True,
            'sessions': history
        })
        
    except Exception as e:
        logger.error(f"History error: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch history',
            'details': str(e)
        }), 500

@api.route('/history/<int:session_id>', methods=['GET'])
@jwt_required
def get_session(session_id):
    """
    Endpoint để lấy chi tiết một session cụ thể
    """
    try:
        logger.debug(f"Getting session {session_id} for user {request.user_id}")
        
        # Truy vấn session
        session = db.session.query(CodeSession)\
            .filter(
                CodeSession.id == session_id,
                CodeSession.user_id == request.user_id
            ).first()
            
        if not session:
            return jsonify({
                'error': 'Session not found'
            }), 404
            
        # Format response
        return jsonify({
            'success': True,
            'session': {
                'id': session.id,
                'query': session.query,
                'code_context': session.code_context,
                'response': session.response,
                'language': session.language,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'tokens_used': session.tokens_used
            }
        })
        
    except Exception as e:
        logger.error(f"Get session error: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch session',
            'details': str(e)
        }), 500

@api.route('/history/<int:session_id>', methods=['DELETE'])
@jwt_required
def delete_session(session_id):
    """
    Endpoint để xóa một session
    """
    try:
        logger.debug(f"Deleting session {session_id} for user {request.user_id}")
        
        # Truy vấn session
        session = db.session.query(CodeSession)\
            .filter(
                CodeSession.id == session_id,
                CodeSession.user_id == request.user_id
            ).first()
            
        if not session:
            return jsonify({
                'error': 'Session not found'
            }), 404
            
        # Xóa session
        db.session.delete(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Session {session_id} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Delete session error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Failed to delete session',
            'details': str(e)
        }), 500

@api.route('/history/clear', methods=['DELETE'])
@jwt_required
def clear_history():
    """
    Endpoint để xóa toàn bộ lịch sử của user
    """
    try:
        logger.debug(f"Clearing history for user {request.user_id}")
        
        # Xóa tất cả sessions của user
        db.session.query(CodeSession)\
            .filter(CodeSession.user_id == request.user_id)\
            .delete()
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'History cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Clear history error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Failed to clear history',
            'details': str(e)
        }), 500