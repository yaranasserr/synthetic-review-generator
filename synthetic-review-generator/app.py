#!/usr/bin/env python3
"""Flask API wrapper for synthetic review generation"""

import os
import sys
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import yaml

sys.path.append('src')

from generator import ReviewGenerator
from reports import generate_quality_report, generate_comparison_report

load_dotenv()

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
CORS(app)

# Global generator instance
generator = None


def init_generator():
    """Initialize generator on first request"""
    global generator
    if generator is None:
        generator = ReviewGenerator(verbose=False)


@app.route('/')
def index():
    """Serve the web UI"""
    return render_template('index.html')


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "synthetic-review-generator",
        "version": "1.0.0"
    })


@app.route('/api/generate/single', methods=['POST'])
def generate_single():
    """Generate a single review"""
    init_generator()
    
    try:
        data = request.get_json() or {}
        force_bad = data.get('force_bad', False)
        
        review = generator.generate_one_raw(force_bad=force_bad)
        
        return jsonify({
            "success": True,
            "review": review
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/generate/batch', methods=['POST'])
def generate_batch():
    """Generate multiple reviews with quality checks"""
    init_generator()
    
    try:
        data = request.get_json() or {}
        count = data.get('count', 10)
        
        if count > 100:
            return jsonify({
                "success": False,
                "error": "Maximum 100 reviews per batch request"
            }), 400
        
        result = generator.generate_all(count=count)
        
        return jsonify({
            "success": True,
            "result": {
                "success_count": result['success_count'],
                "skipped_count": result['skipped_count'],
                "clean_path": result['clean_path'],
                "with_models_path": result['with_models_path'],
                "csv_log": result['csv_log'],
                "timestamp": result['timestamp']
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quality-check', methods=['POST'])
def quality_check():
    """Check quality of a provided review"""
    init_generator()
    
    try:
        data = request.get_json()
        review = data.get('review')
        existing_reviews = data.get('existing_reviews', [])
        
        if not review:
            return jsonify({
                "success": False,
                "error": "Review object is required"
            }), 400
        
        result = generator.quality.check_all(review, existing_reviews)
        
        return jsonify({
            "success": True,
            "quality_check": result
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/reports/quality', methods=['POST'])
def create_quality_report():
    """Generate quality report from latest generation"""
    try:
        import glob
        from pathlib import Path
        
        # Find latest CSV log
        logs_dir = Path("data/synthetic/logs")
        csv_files = list(logs_dir.glob("generation_log_*.csv"))
        
        if not csv_files:
            return jsonify({
                "success": False,
                "error": "No generation logs found. Generate reviews first."
            }), 404
        
        # Get most recent CSV
        latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
        
        # Find corresponding synthetic reviews
        timestamp = latest_csv.stem.replace("generation_log_", "")
        synthetic_path = f"data/synthetic/reviews/reviews_clean_{timestamp}.json"
        
        if not os.path.exists(synthetic_path):
            # Try to find any recent synthetic file
            reviews_dir = Path("data/synthetic/reviews")
            synthetic_files = list(reviews_dir.glob("reviews_clean_*.json"))
            if synthetic_files:
                synthetic_path = str(max(synthetic_files, key=lambda p: p.stat().st_mtime))
            else:
                synthetic_path = None
        
        # Real reviews path
        real_path = "data/raw/real_reviews.json"
        
        # Generate report
        report_path, report_text = generate_quality_report(
            str(latest_csv),
            include_charts=False,
            synthetic_path=synthetic_path,
            real_path=real_path if os.path.exists(real_path) else None
        )
        
        return jsonify({
            "success": True,
            "report_path": report_path,
            "report_text": report_text,
            "csv_used": str(latest_csv),
            "synthetic_used": synthetic_path,
            "real_used": real_path if os.path.exists(real_path) else None
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/reports/comparison', methods=['POST'])
def create_comparison_report():
    """Generate comparison report using latest synthetic and real reviews"""
    try:
        from pathlib import Path
        
        # Find latest synthetic reviews
        reviews_dir = Path("data/synthetic/reviews")
        synthetic_files = list(reviews_dir.glob("reviews_clean_*.json"))
        
        if not synthetic_files:
            return jsonify({
                "success": False,
                "error": "No synthetic reviews found. Generate reviews first."
            }), 404
        
        synthetic_path = str(max(synthetic_files, key=lambda p: p.stat().st_mtime))
        
        # Real reviews path
        real_path = "data/raw/real_reviews.json"
        
        if not os.path.exists(real_path):
            return jsonify({
                "success": False,
                "error": "Real reviews not found at data/raw/real_reviews.json"
            }), 404
        
        # Generate comparison report
        report_path, report_text = generate_comparison_report(
            real_path,
            synthetic_path,
            include_charts=False
        )
        
        return jsonify({
            "success": True,
            "report_path": report_path,
            "report_text": report_text,
            "synthetic_used": synthetic_path,
            "real_used": real_path
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/files/list', methods=['GET'])
def list_files():
    """List all generated files"""
    try:
        from pathlib import Path
        
        files = {
            "csv_logs": [],
            "synthetic_reviews": [],
            "synthetic_with_models": [],
            "reports": []
        }
        
        # CSV logs
        logs_dir = Path("data/synthetic/logs")
        if logs_dir.exists():
            files["csv_logs"] = [
                {
                    "path": str(f),
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": f.stat().st_mtime
                }
                for f in sorted(logs_dir.glob("generation_log_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
            ]
        
        # Synthetic reviews (clean)
        reviews_dir = Path("data/synthetic/reviews")
        if reviews_dir.exists():
            files["synthetic_reviews"] = [
                {
                    "path": str(f),
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": f.stat().st_mtime
                }
                for f in sorted(reviews_dir.glob("reviews_clean_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            ]
        
        # Synthetic with models
        models_dir = Path("data/synthetic/reviews_models")
        if models_dir.exists():
            files["synthetic_with_models"] = [
                {
                    "path": str(f),
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": f.stat().st_mtime
                }
                for f in sorted(models_dir.glob("reviews_with_models_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            ]
        
        # Reports
        outputs_dir = Path("outputs")
        if outputs_dir.exists():
            files["reports"] = [
                {
                    "path": str(f),
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": f.stat().st_mtime
                }
                for f in sorted(outputs_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            ]
        
        return jsonify({
            "success": True,
            "files": files
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    try:
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        return jsonify({
            "success": True,
            "config": config
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/files/<path:filepath>', methods=['GET'])
def download_file(filepath):
    """Download generated files"""
    try:
        if not os.path.exists(filepath):
            return jsonify({
                "success": False,
                "error": "File not found"
            }), 404
        
        return send_file(filepath, as_attachment=True)
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


if __name__ == '__main__':
   
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not found in .env")
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not found in .env")
    
    # Run server
    port = int(os.getenv('PORT', 4800))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"\n🚀 Synthetic Review Generator API")
    print(f"📍 Web UI: http://localhost:{port}")
    print(f"📍 API: http://localhost:{port}/api")
    print(f"\n📚 API Endpoints:")
    print(f"   GET  /health                   - Health check")
    print(f"   POST /api/generate/single      - Generate one review")
    print(f"   POST /api/generate/batch       - Generate multiple reviews")
    print(f"   POST /api/quality-check        - Check review quality")
    print(f"   POST /api/reports/quality      - Generate quality report")
    print(f"   POST /api/reports/comparison   - Generate comparison report")
    print(f"   GET  /api/config               - Get configuration")
    print(f"   GET  /api/files/<path>         - Download generated files\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)