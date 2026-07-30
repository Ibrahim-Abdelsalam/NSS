import os
import sys
# Add project root to path so 'experiments' can be imported when running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import numpy as np
import pulp
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QFormLayout, QSpinBox, QDoubleSpinBox, QPushButton, QTextEdit, 
    QTableWidget, QTableWidgetItem, QGroupBox, QLabel, QSplitter, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QTextDocument
from PyQt5.QtPrintSupport import QPrinter

from experiments.frost_ns_submodel.model import build_frost_ns_model
from experiments.frost_ns_submodel.verification import verify_rostering

class SolverWorker(QThread):
    finished = pyqtSignal(object, str, object, object, object, object, object)
    
    def __init__(self, params, nurses, days, shifts, scenarios, demand):
        super().__init__()
        self.params = params
        self.nurses = nurses
        self.days = days
        self.shifts = shifts
        self.scenarios = scenarios
        self.demand = demand
        
    def run(self):
        try:
            prob = build_frost_ns_model(
                self.nurses, self.days, self.shifts, 
                self.scenarios, self.demand, self.params
            )
            solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=60)
            prob.solve(solver)
            
            status = pulp.LpStatus[prob.status]
            self.finished.emit(prob, status, self.nurses, self.days, self.shifts, self.scenarios, self.demand)
        except Exception as e:
            self.finished.emit(None, f"Error: {str(e)}", None, None, None, None, None)


class FrostNSMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FROST-NS Prototype Simulator")
        self.resize(1100, 700)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # LEFT PANEL (Inputs)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # -- 1. Data Config --
        data_group = QGroupBox("Instance Configuration")
        data_form = QFormLayout()
        self.inp_nurses = QSpinBox(); self.inp_nurses.setRange(1, 50); self.inp_nurses.setValue(6)
        self.inp_days = QSpinBox(); self.inp_days.setRange(1, 28); self.inp_days.setValue(7)
        self.inp_shifts = QSpinBox(); self.inp_shifts.setRange(1, 5); self.inp_shifts.setValue(3)
        self.inp_scenarios = QSpinBox(); self.inp_scenarios.setRange(1, 50); self.inp_scenarios.setValue(3)
        data_form.addRow("Number of Nurses:", self.inp_nurses)
        data_form.addRow("Planning Days:", self.inp_days)
        data_form.addRow("Shift Types:", self.inp_shifts)
        data_form.addRow("Scenarios:", self.inp_scenarios)
        data_group.setLayout(data_form)
        left_layout.addWidget(data_group)
        
        # -- 2. Illustrative Scenarios Generator --
        gen_group = QGroupBox("Generate Illustrative Scenarios")
        gen_layout = QVBoxLayout()
        gen_form = QFormLayout()
        self.inp_base_demand = QSpinBox(); self.inp_base_demand.setRange(1, 20); self.inp_base_demand.setValue(2)
        self.inp_var = QDoubleSpinBox(); self.inp_var.setRange(0, 1); self.inp_var.setSingleStep(0.05); self.inp_var.setValue(0.20)
        self.inp_seed = QSpinBox(); self.inp_seed.setRange(0, 9999); self.inp_seed.setValue(42)
        gen_form.addRow("Base Demand (per shift):", self.inp_base_demand)
        gen_form.addRow("Variation Level (+/-):", self.inp_var)
        gen_form.addRow("Random Seed:", self.inp_seed)
        gen_layout.addLayout(gen_form)
        
        # Preset buttons for synthetic cases
        presets_layout = QHBoxLayout()
        btn_case_low = QPushButton("Low Var Case")
        btn_case_low.clicked.connect(lambda: (self.inp_base_demand.setValue(2), self.inp_var.setValue(0.10)))
        btn_case_high = QPushButton("High Var Case")
        btn_case_high.clicked.connect(lambda: (self.inp_base_demand.setValue(2), self.inp_var.setValue(0.60)))
        btn_case_heavy = QPushButton("Heavy Demand Case")
        btn_case_heavy.clicked.connect(lambda: (self.inp_base_demand.setValue(4), self.inp_var.setValue(0.30)))
        presets_layout.addWidget(btn_case_low)
        presets_layout.addWidget(btn_case_high)
        presets_layout.addWidget(btn_case_heavy)
        gen_layout.addLayout(presets_layout)
        
        gen_group.setLayout(gen_layout)
        left_layout.addWidget(gen_group)
        
        # -- 3. Work Limits --
        limits_group = QGroupBox("Work Limits")
        limits_form = QFormLayout()
        self.inp_w_bar = QSpinBox(); self.inp_w_bar.setRange(1, 50); self.inp_w_bar.setValue(5)
        self.inp_n_bar = QSpinBox(); self.inp_n_bar.setRange(1, 20); self.inp_n_bar.setValue(2)
        self.inp_c_bar = QSpinBox(); self.inp_c_bar.setRange(1, 10); self.inp_c_bar.setValue(3)
        limits_form.addRow("Max Shifts (W_bar):", self.inp_w_bar)
        limits_form.addRow("Max Nights (N_bar):", self.inp_n_bar)
        limits_form.addRow("Max Consec. Days (C_bar):", self.inp_c_bar)
        limits_group.setLayout(limits_form)
        left_layout.addWidget(limits_group)
        
        # -- 4. Fatigue & Fairness --
        fairness_group = QGroupBox("Fatigue & Fairness")
        fairness_form = QFormLayout()
        self.inp_f_bar = QSpinBox(); self.inp_f_bar.setRange(1, 50); self.inp_f_bar.setValue(6)
        self.inp_d_w = QSpinBox(); self.inp_d_w.setRange(0, 10); self.inp_d_w.setValue(2)
        self.inp_d_n = QSpinBox(); self.inp_d_n.setRange(0, 10); self.inp_d_n.setValue(1)
        fairness_form.addRow("Fatigue Cap (F_bar):", self.inp_f_bar)
        fairness_form.addRow("Workload Gap (Delta_W):", self.inp_d_w)
        fairness_form.addRow("Night Gap (Delta_N):", self.inp_d_n)
        fairness_group.setLayout(fairness_form)
        left_layout.addWidget(fairness_group)
        
        # -- 5. Demand Response & Costs --
        resp_group = QGroupBox("Demand Response & CVaR")
        resp_form = QFormLayout()
        self.inp_a_bar = QSpinBox(); self.inp_a_bar.setRange(0, 10); self.inp_a_bar.setValue(2)
        self.inp_alpha = QDoubleSpinBox(); self.inp_alpha.setRange(0.01, 0.99); self.inp_alpha.setValue(0.80)
        self.inp_tau = QSpinBox(); self.inp_tau.setRange(0, 500); self.inp_tau.setValue(20)
        resp_form.addRow("Emerg. Cap (a_bar):", self.inp_a_bar)
        resp_form.addRow("CVaR Level (alpha):", self.inp_alpha)
        resp_form.addRow("Max CVaR Limit (tau):", self.inp_tau)
        resp_group.setLayout(resp_form)
        left_layout.addWidget(resp_group)
        
        # Action button
        self.btn_solve = QPushButton("Optimize Schedule")
        self.btn_solve.clicked.connect(self.run_optimization)
        self.btn_solve.setStyleSheet("background-color: #2b6cb0; color: white; padding: 10px; font-weight: bold;")
        left_layout.addWidget(self.btn_solve)
        left_layout.addStretch()
        
        # RIGHT PANEL (Outputs)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.lbl_status = QLabel("Ready.")
        self.lbl_status.setStyleSheet("font-weight: bold; color: #4a5568;")
        right_layout.addWidget(self.lbl_status)
        
        self.table_roster = QTableWidget()
        right_layout.addWidget(QLabel("Baseline Roster:"))
        right_layout.addWidget(self.table_roster, stretch=1)
        
        self.text_console = QTextEdit()
        self.text_console.setReadOnly(True)
        self.text_console.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: monospace;")
        right_layout.addWidget(QLabel("Verification & Audit Log:"))
        right_layout.addWidget(self.text_console, stretch=1)
        
        self.btn_export = QPushButton("Export to PDF")
        self.btn_export.clicked.connect(self.export_pdf)
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("background-color: #38a169; color: white; padding: 10px; font-weight: bold;")
        right_layout.addWidget(self.btn_export)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 750])

    def validate_inputs(self):
        w = self.inp_w_bar.value()
        f = self.inp_f_bar.value()
        if f < w:
            QMessageBox.warning(self, "Input Error",
                f"The fatigue cap (F_bar={f}) must be at least the permitted number of shifts (W_bar={w}).\n"
                f"→ Recommendation: Increase F_bar to at least {w}.")
            return False
        return True

    def diagnose_infeasibility(self, nurses, days, shifts, scenarios, demand, params):
        """
        Runs analytical checks on the instance before (or after) solving
        and returns a list of (cause, recommendation) tuples for every
        infeasibility risk found.
        """
        issues = []
        n_nurses  = len(nurses)
        n_days    = len(days)
        n_shifts  = len(shifts)
        n_scen    = len(scenarios)
        W_bar     = params['W_bar']
        N_bar     = params['N_bar']
        C_bar     = params['C_bar']
        F_bar     = params['F_bar']
        Delta_W   = params['Delta_W']
        Delta_N   = params['Delta_N']
        a_bar     = params['a_bar']
        alpha     = params['alpha']
        tau       = params['tau']
        night_k   = params['night_shift_id']

        # --- 1. Total capacity vs average demand ---
        max_planned_shifts = n_nurses * W_bar
        total_slots        = n_days * n_shifts
        avg_demand_per_slot = (
            sum(demand.values()) / (n_scen * n_days * n_shifts)
            if demand else 0
        )
        avg_total_demand = avg_demand_per_slot * total_slots
        max_total_coverage = max_planned_shifts + a_bar * total_slots
        if max_total_coverage < avg_total_demand:
            shortfall = avg_total_demand - max_total_coverage
            issues.append((
                "Capacity-Demand Gap",
                f"Even filling every shift with emergency staff, total coverage "
                f"({max_total_coverage:.0f}) is less than average total demand "
                f"({avg_total_demand:.0f}). Shortfall ≈ {shortfall:.0f} shifts.\n"
                f"  → Increase W_bar (currently {W_bar}) so nurses can work more shifts, OR\n"
                f"  → Increase a_bar (currently {a_bar}) for more emergency capacity, OR\n"
                f"  → Reduce the Number of Nurses' Max Shifts to raise coverage, OR\n"
                f"  → Use fewer planning days or a lower Base Demand."
            ))

        # --- 2. CVaR limit too tight ---
        # Worst-case (highest-demand) scenario
        worst_total_demand = 0
        for omega in scenarios:
            sc_demand = sum(demand.get((j, k, omega), 0) for j in days for k in shifts)
            if sc_demand > worst_total_demand:
                worst_total_demand = sc_demand
        min_unmet = max(0, worst_total_demand - max_total_coverage)
        if min_unmet > 0:
            # CVaR >= min_unmet when every scenario has the same loss
            # (lower bound; actual CVaR could be higher)
            cvar_lower = min_unmet
            if cvar_lower > tau:
                issues.append((
                    "CVaR Limit Impossible to Satisfy",
                    f"In the worst scenario, at least {min_unmet:.0f} shifts will be unmet "
                    f"even with maximum emergency staffing. The computed CVaR will exceed "
                    f"tau={tau}.\n"
                    f"  → Increase tau (currently {tau}) to ≥ {int(min_unmet)+1}, OR\n"
                    f"  → Increase a_bar or W_bar to reduce unavoidable unmet demand, OR\n"
                    f"  → Lower alpha (currently {alpha}) to be less conservative."
                ))

        # --- 3. Consecutive-day limit vs scheduling enough shifts ---
        # Max shifts schedulable per nurse given C_bar
        # Worst case: C_bar on, 1 off, repeating
        cycle = C_bar + 1
        max_shifts_from_consec = (n_days // cycle) * C_bar + min(C_bar, n_days % cycle)
        if max_shifts_from_consec < W_bar:
            issues.append((
                "W_bar Unreachable Due to Consecutive-Day Limit",
                f"With C_bar={C_bar} and {n_days} planning days, a nurse can work at most "
                f"{max_shifts_from_consec} shifts (not {W_bar}) before the consecutive limit "
                f"forces a day off.\n"
                f"  → Reduce W_bar to ≤ {max_shifts_from_consec}, OR\n"
                f"  → Increase C_bar to allow longer working runs."
            ))

        # --- 4. Night cap vs. N_bar with fairness ---
        # If Delta_N=0, all nurses must have exactly the same night count.
        # If N_bar is 0 but a night shift exists among K, nurses can't be assigned nights.
        if N_bar == 0 and night_k in shifts:
            issues.append((
                "Night Shifts Blocked (N_bar=0)",
                f"N_bar is 0, meaning no nurse can work the night shift ({night_k}).\n"
                f"  → Increase N_bar to allow night coverage."
            ))

        # --- 5. Workload fairness gap vs. W_bar ---
        # If Delta_W=0 all nurses must work exactly the same number of shifts.
        # This can conflict with odd nurse counts or demand patterns.
        if Delta_W == 0 and avg_total_demand % n_nurses != 0:
            issues.append((
                "Strict Workload Fairness May Be Infeasible",
                f"Delta_W=0 requires all {n_nurses} nurses to work exactly the same number "
                f"of shifts, but average demand ({avg_total_demand:.0f}) is not evenly divisible "
                f"by {n_nurses} nurses.\n"
                f"  → Increase Delta_W to 1 or 2 to allow slight imbalance."
            ))

        # --- 6. Night fairness gap vs. available nights ---
        # Total night slots available
        total_night_slots = n_days * 1  # 1 night shift per day
        if Delta_N == 0 and total_night_slots % n_nurses != 0:
            issues.append((
                "Strict Night Fairness May Be Infeasible",
                f"Delta_N=0 requires all {n_nurses} nurses to work exactly the same number "
                f"of night shifts, but {total_night_slots} night slots don't divide evenly "
                f"among {n_nurses} nurses.\n"
                f"  → Increase Delta_N to 1 to allow minor imbalance."
            ))

        # --- 7. Fatigue cap too low ---
        if F_bar < W_bar:
            issues.append((
                "Fatigue Cap Below Max Shifts (F_bar < W_bar)",
                f"F_bar={F_bar} prevents nurses from reaching W_bar={W_bar} shifts. "
                f"The fatigue score equals total shifts + night shifts, so if F_bar < W_bar, "
                f"nurses are forced to work fewer shifts than allowed.\n"
                f"  → Set F_bar ≥ W_bar (at minimum). F_bar ≥ W_bar + N_bar is recommended."
            ))

        # --- 8. alpha=1.0 edge case ---
        if alpha >= 1.0:
            issues.append((
                "CVaR Alpha = 1.0 Is Undefined",
                f"alpha={alpha} makes the CVaR denominator (1-alpha)=0, which is mathematically "
                f"undefined and will cause a division-by-zero in the model.\n"
                f"  → Use alpha ≤ 0.99."
            ))

        return issues

    def generate_scenarios(self, n_days, shifts, n_scenarios):
        np.random.seed(self.inp_seed.value())
        base = self.inp_base_demand.value()
        var = self.inp_var.value()
        
        demand = {}
        for j in range(1, n_days + 1):
            for k in shifts:
                for omega in range(1, n_scenarios + 1):
                    variation = np.random.uniform(-var, var)
                    val = max(0, int(round(base * (1 + variation))))
                    demand[(j, k, omega)] = val
        return demand

    def run_optimization(self):
        if not self.validate_inputs():
            return
            
        self.btn_solve.setEnabled(False)
        self.btn_solve.setText("Solving...")
        self.lbl_status.setText("Solver running in background...")
        self.text_console.clear()
        self.table_roster.clear()
        
        # Construct data
        n_nurses = self.inp_nurses.value()
        n_days = self.inp_days.value()
        n_shifts = self.inp_shifts.value()
        n_scenarios = self.inp_scenarios.value()
        
        nurses = [f"N{i+1}" for i in range(n_nurses)]
        days = list(range(1, n_days + 1))
        
        # Shift types (e.g. S1, S2, S3, where the last is Night)
        shifts = [f"S{i+1}" for i in range(n_shifts)]
        night_shift_id = shifts[-1]
        scenarios = list(range(1, n_scenarios + 1))
        
        demand = self.generate_scenarios(n_days, shifts, n_scenarios)
        
        # Probabilities
        p_omega = {w: 1.0/n_scenarios for w in scenarios}
        
        # Q matrix (all qualified)
        q = {(i, k): 1 for i in nurses for k in shifts}
        
        # Weights (all 1.0)
        w_k = {k: 1.0 for k in shifts}
        
        params = {
            'W_bar': self.inp_w_bar.value(),
            'N_bar': self.inp_n_bar.value(),
            'C_bar': self.inp_c_bar.value(),
            'F_bar': self.inp_f_bar.value(),
            'Delta_W': self.inp_d_w.value(),
            'Delta_N': self.inp_d_n.value(),
            'alpha': self.inp_alpha.value(),
            'tau': self.inp_tau.value(),
            'a_bar': self.inp_a_bar.value(),
            'c_planned': 100,
            'c_emergency': 200,
            'c_unmet': 300,
            'night_shift_id': night_shift_id,
            'p_omega': p_omega,
            'q': q,
            'w': w_k
        }
        
        self.worker = SolverWorker(params, nurses, days, shifts, scenarios, demand)
        self.worker.finished.connect(self.on_solve_finished)
        self.worker.start()

    def on_solve_finished(self, prob, status, nurses, days, shifts, scenarios, demand):
        self.btn_solve.setEnabled(True)
        self.btn_solve.setText("Optimize Schedule")
        
        if prob is None or status not in ['Optimal', 'Feasible']:
            self.lbl_status.setText(f"Solve Failed/Infeasible. Status: {status}")

            report = "Optimization did not return a feasible schedule.\n"
            report += f"Solver status: {status}\n"
            report += "=" * 50 + "\n\n"

            # Only run diagnostics if we have real instance data (not a crash)
            if nurses is not None and demand is not None:
                issues = self.diagnose_infeasibility(
                    nurses, days, shifts, scenarios, demand, self.worker.params
                )
                if issues:
                    report += f"Diagnosed {len(issues)} potential cause(s) of infeasibility:\n\n"
                    for i, (cause, rec) in enumerate(issues, 1):
                        report += f"[{i}] {cause}\n"
                        report += f"    {rec}\n\n"
                else:
                    report += (
                        "No obvious structural cause detected.\n"
                        "The infeasibility may arise from a combination of tight fairness,\n"
                        "consecutive-day, and CVaR constraints interacting together.\n\n"
                        "Try relaxing one constraint at a time:\n"
                        "  → Increase Delta_W or Delta_N by 1\n"
                        "  → Increase W_bar or a_bar\n"
                        "  → Increase tau\n"
                        "  → Reduce Base Demand or switch to Low Var Case"
                    )
            else:
                report += (
                    "The solver encountered an internal error before completing.\n"
                    "Check that PuLP and CBC are installed correctly."
                )

            self.text_console.setText(report)
            return
            
        self.lbl_status.setText(f"Status: {status} | Objective: {pulp.value(prob.objective):.2f}")
        
        # Render Table
        self.table_roster.setRowCount(len(nurses))
        self.table_roster.setColumnCount(len(days))
        self.table_roster.setHorizontalHeaderLabels([f"Day {j}" for j in days])
        self.table_roster.setVerticalHeaderLabels(nurses)
        
        x = prob._vars['x']
        for row, i in enumerate(nurses):
            for col, j in enumerate(days):
                assigned_shift = "-"
                for k in shifts:
                    if pulp.value(x[i][j][k]) > 0.5:
                        assigned_shift = k
                        break
                
                item = QTableWidgetItem(assigned_shift)
                item.setTextAlignment(Qt.AlignCenter)
                if assigned_shift != "-":
                    idx = shifts.index(assigned_shift)
                    colors = [QColor(173, 216, 230), QColor(144, 238, 144), QColor(255, 200, 150), QColor(255, 182, 193)]
                    item.setBackground(colors[idx % len(colors)])
                    item.setForeground(QColor(0, 0, 0))
                else:
                    item.setBackground(QColor(240, 240, 240))
                    item.setForeground(QColor(150, 150, 150))
                self.table_roster.setItem(row, col, item)
        self.table_roster.resizeColumnsToContents()
        
        # Verification Audit
        passed, report = verify_rostering(prob, nurses, days, shifts, scenarios, demand, self.worker.params)
        
        audit_text = "=================================================\n"
        audit_text += " FROST-NS PROTOTYPE AUDIT REPORT\n"
        audit_text += "=================================================\n\n"
        audit_text += report
        audit_text += f"\n\nOverall Satisfaction: {'PASSED' if passed else 'FAILED'}"
        
        self.text_console.setText(audit_text)
        self.btn_export.setEnabled(True)

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
            
        html = "<h1>FROST-NS Prototype Schedule</h1>"
        html += "<table border='1' cellspacing='0' cellpadding='5'>"
        html += "<tr><th>Nurse</th>"
        for j in range(self.table_roster.columnCount()):
            html += f"<th>{self.table_roster.horizontalHeaderItem(j).text()}</th>"
        html += "</tr>"
        
        for i in range(self.table_roster.rowCount()):
            html += f"<tr><td><b>{self.table_roster.verticalHeaderItem(i).text()}</b></td>"
            for j in range(self.table_roster.columnCount()):
                item = self.table_roster.item(i, j)
                text = item.text() if item else ""
                bg_col = "#ffffff"
                if item and item.background().color().isValid():
                    bg_col = item.background().color().name()
                html += f"<td style='background-color: {bg_col}; text-align: center;'>{text}</td>"
            html += "</tr>"
        html += "</table>"
        
        html += "<h2>Audit Log</h2>"
        html += f"<pre>{self.text_console.toPlainText()}</pre>"
        
        doc = QTextDocument()
        doc.setHtml(html)
        
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        printer.setOrientation(QPrinter.Portrait)
        doc.print_(printer)
        
        QMessageBox.information(self, "Export Success", f"Successfully exported to:\n{path}")


def run_gui():
    app = QApplication(sys.argv)
    window = FrostNSMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_gui()
