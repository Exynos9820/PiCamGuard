from flask import Blueprint, render_template

bp = Blueprint("plots", __name__)

@bp.route("/plots")
def plots_page():
    return render_template("plots.html")
