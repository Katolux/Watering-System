from flask import Blueprint


plant_bp = Blueprint("plant", __name__)


from gardenhub.routes.plants import catalog, editor, varieties
