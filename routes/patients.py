from flask import Blueprint, request, redirect, url_for, render_template, jsonify, session
from models.patient import Patient
from utils.database import get_db_connection
from routes.diagnoses import get_diagnosis
from routes.doctors import get_doctors
from routes.companies import get_companies
from routes.insurances import get_insurances

patient_bp = Blueprint("patient", __name__)

@patient_bp.route('/patient/create', methods=['GET', 'POST'])
def create_patient():
    if request.method == 'POST':
        data = request.form
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO pacienti (
                meno, rodne_cislo, adresa, poistovna, ados,
                sestra, odosielatel, pohlavie, cislo_dekurzu, diagnoza
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data['meno'], data['rodne_cislo'], data['adresa'], data['poistovna'],
                data['ados'], data['sestra'], data['odosielatel'],
                data['pohlavie'], data['cislo_dekurzu'], data['diagnoza']
            ))
        conn.commit()
        conn.close()
        return redirect(url_for('main.settings'))

    doctors = get_doctors()
    insurances = get_insurances()
    companies = get_companies()
    return render_template("create/patient.html",doctors=doctors, insurances=insurances, companies=companies)

@patient_bp.route('/patient/update/<int:id>', methods=['GET', 'POST'])
def update_patient(id):
    if request.method == 'POST':
        data = request.form
        conn = get_db_connection()
        conn.execute("""
            UPDATE pacienti SET
                meno = ?, rodne_cislo = ?, adresa = ?, poistovna = ?, ados = ?,
                sestra = ?, odosielatel = ?, pohlavie = ?, cislo_dekurzu = ?, diagnoza = ?
            WHERE id = ?""",
            (
                data['meno'], data['rodne_cislo'], data['adresa'], data['poistovna'],
                data['ados'], data['sestra'], data['odosielatel'],
                data['pohlavie'], data['cislo_dekurzu'], data['diagnoza'], id
            ))
        conn.commit()
        conn.close()
        return redirect(url_for('patient.list_patients'))

    patient = get_patient(id)
    if not patient:
        return "Pacient nenájdený", 404

    doctors = get_doctors()
    insurances = get_insurances()
    companies = get_companies()
    diagnosis = get_diagnosis(patient.diagnoza)
    return render_template("details/patient.html", patient=patient, insurances=insurances, doctors=doctors, companies=companies, diagnosis=diagnosis)

@patient_bp.route('/patient/delete/<int:id>', methods=['POST'])
def delete_patient(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM pacienti WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('patient.list_patients'))

@patient_bp.route('/patient/search')
def search_patients():
    query = request.args.get('q', '').strip().lower()
    nurse_id = session.get('nurse', {}).get('id')

    if not nurse_id:
        return jsonify([])

    conn = get_db_connection()
    rows = conn.execute("""
        SELECT * FROM pacienti
        WHERE sestra = ?
        AND (LOWER(meno) LIKE ? OR LOWER(rodne_cislo) LIKE ?)
    """, (nurse_id, f"%{query}%", f"%{query}%")).fetchall()
    conn.close()

    results = [Patient(row).__dict__ for row in rows]
    return jsonify(results)

@patient_bp.route('/patients/list/')
def list_patients():
    patients = get_patients()
    return render_template("details/patients.html", patients=patients)

@patient_bp.route('/patients/menu/')
def menu():
    patients = get_patients()
    return render_template("dekurzy/menu.html", patients=patients)

def get_patients():
    nurse_id = session.get('nurse', {}).get('id')

    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM pacienti WHERE sestra = ?", (nurse_id,)).fetchall()
    conn.close()
    return [Patient(row) for row in rows]

def get_patient(id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM pacienti WHERE id = ?", (id,)).fetchone()
    conn.close()
    return Patient(row) if row else None

def get_patients_in_day(date_str):
    nurse_id = session.get("nurse", {}).get("id")
    month_id = session.get("month", {}).get("id")
    if not nurse_id or not month_id or not date_str:
        return []

    conn = get_db_connection()
    rows = conn.execute("""
        SELECT p.*, dp.vysetrenie, dp.vypis
        FROM den-pacient dp
        JOIN dni d ON dp.den_id = d.id
        JOIN pacienti p ON dp.patient_id = p.id
        WHERE d.mesiac = ? AND d.datum = ?
    """, (month_id, date_str)).fetchall()
    conn.close()
    return rows

def get_patients_in_month():
    nurse_id = session.get("nurse", {}).get("id")
    month_id = session.get("month", {}).get("id")
    if not nurse_id or not month_id:
        return []

    conn = get_db_connection()
    rows = conn.execute("""
        SELECT DISTINCT p.*
        FROM den-pacient dp
        JOIN dni d ON dp.den_id = d.id
        JOIN pacienti p ON dp.patient_id = p.id
        WHERE d.mesiac = ?
    """, (month_id,)).fetchall()
    conn.close()
    return rows
