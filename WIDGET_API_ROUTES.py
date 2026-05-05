"""
Widget Dashboard API Routes
Add these routes to web/app.py after the existing routes

COPY AND PASTE these routes into web/app.py in the appropriate section
"""

# PASTE THIS INTO web/app.py after the existing routes:

# ==================== WIDGET DASHBOARD ROUTES ====================

from widgets_db import (
    init_widgets_db, create_widget, get_user_widgets, 
    update_widget, delete_widget, update_widget_positions,
    get_widget_by_id, reset_user_dashboard
)
from widget_renderers import WidgetRenderer

@app.route('/api/widgets', methods=['GET', 'POST'])
def manage_widgets():
    """Get all widgets or create a new widget"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        user_id = session['user_id']
        
        if request.method == 'POST':
            data = request.json
            widget_type = data.get('type', '').strip()
            config = data.get('config', {})
            position_x = data.get('position_x', 0)
            position_y = data.get('position_y', 0)
            width = data.get('width', 4)
            height = data.get('height', 4)
            
            if not widget_type or widget_type not in ['todo', 'habit', 'focus']:
                return jsonify({'error': 'Invalid widget type'}), 400
            
            try:
                widget_id = create_widget(
                    user_id, widget_type, config,
                    position_x, position_y, width, height
                )
                logging.info(f"✓ Widget created: id={widget_id}, user={user_id}, type={widget_type}")
                
                # Render the new widget
                rendered = WidgetRenderer.render_widget(widget_id, widget_type, user_id, config)
                rendered['id'] = widget_id
                
                return jsonify({
                    'id': widget_id,
                    'status': 'created',
                    'widget': rendered
                }), 201
            except Exception as e:
                logging.error(f"✗ Widget creation failed: {e}")
                return jsonify({
                    'error': 'Failed to create widget',
                    'details': str(e) if os.getenv("DEBUG") else "Server error"
                }), 500
        
        else:  # GET
            try:
                widgets = get_user_widgets(user_id)
                
                # Render each widget with data
                rendered_widgets = []
                for widget in widgets:
                    rendered = WidgetRenderer.render_widget(
                        widget['id'],
                        widget['type'],
                        user_id,
                        widget.get('config', {})
                    )
                    rendered['id'] = widget['id']
                    rendered['position_x'] = widget['position_x']
                    rendered['position_y'] = widget['position_y']
                    rendered['width'] = widget['width']
                    rendered['height'] = widget['height']
                    rendered_widgets.append(rendered)
                
                logging.info(f"✓ Widgets fetched: count={len(widgets)}, user={user_id}")
                return jsonify({'widgets': rendered_widgets})
            except Exception as e:
                logging.error(f"✗ Widget fetch failed: {e}")
                return jsonify({
                    'error': 'Failed to load widgets',
                    'details': str(e) if os.getenv("DEBUG") else "Server error"
                }), 500
    
    except Exception as e:
        logging.error(f"✗ Widgets endpoint error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/widgets/<int:widget_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_single_widget(widget_id):
    """Get, update, or delete a specific widget"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        user_id = session['user_id']
        
        if request.method == 'GET':
            try:
                widget = get_widget_by_id(widget_id, user_id)
                if not widget:
                    return jsonify({'error': 'Widget not found'}), 404
                
                rendered = WidgetRenderer.render_widget(
                    widget['id'],
                    widget['type'],
                    user_id,
                    widget.get('config', {})
                )
                rendered['id'] = widget['id']
                rendered['position_x'] = widget['position_x']
                rendered['position_y'] = widget['position_y']
                rendered['width'] = widget['width']
                rendered['height'] = widget['height']
                
                return jsonify(rendered)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'PUT':
            try:
                data = request.json
                update_data = {}
                
                if 'config' in data:
                    update_data['config'] = data['config']
                if 'position_x' in data:
                    update_data['position_x'] = data['position_x']
                if 'position_y' in data:
                    update_data['position_y'] = data['position_y']
                if 'width' in data:
                    update_data['width'] = data['width']
                if 'height' in data:
                    update_data['height'] = data['height']
                
                if not update_data:
                    return jsonify({'error': 'No valid fields to update'}), 400
                
                update_widget(widget_id, user_id, **update_data)
                logging.info(f"✓ Widget updated: id={widget_id}, user={user_id}")
                
                return jsonify({'status': 'updated', 'id': widget_id})
            except ValueError as ve:
                return jsonify({'error': str(ve)}), 404
            except Exception as e:
                logging.error(f"✗ Widget update failed: {e}")
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'DELETE':
            try:
                success = delete_widget(widget_id, user_id)
                if not success:
                    return jsonify({'error': 'Widget not found'}), 404
                
                logging.info(f"✓ Widget deleted: id={widget_id}, user={user_id}")
                return jsonify({'status': 'deleted', 'id': widget_id})
            except Exception as e:
                logging.error(f"✗ Widget deletion failed: {e}")
                return jsonify({'error': str(e)}), 500
    
    except Exception as e:
        logging.error(f"✗ Widget single endpoint error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/widgets/positions', methods=['POST'])
def update_widgets_positions():
    """Update positions for multiple widgets at once"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        user_id = session['user_id']
        data = request.json
        positions = data.get('positions', [])
        
        if not positions:
            return jsonify({'error': 'No positions provided'}), 400
        
        try:
            update_widget_positions(user_id, positions)
            logging.info(f"✓ Widget positions updated: count={len(positions)}, user={user_id}")
            return jsonify({'status': 'positions_updated', 'count': len(positions)})
        except Exception as e:
            logging.error(f"✗ Position update failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    except Exception as e:
        logging.error(f"✗ Positions endpoint error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/widgets/reset', methods=['POST'])
def reset_dashboard():
    """Reset dashboard to empty state"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        user_id = session['user_id']
        
        try:
            reset_user_dashboard(user_id)
            logging.info(f"✓ Dashboard reset: user={user_id}")
            return jsonify({'status': 'dashboard_reset'})
        except Exception as e:
            logging.error(f"✗ Reset failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    except Exception as e:
        logging.error(f"✗ Reset endpoint error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/dashboard')
def dashboard():
    """Render the widget-based dashboard page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = get_user(user_id)
    
    if not user:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', 
                         user_name=user[1] if user and len(user) > 1 else "User")

# ==================== END WIDGET ROUTES ====================
