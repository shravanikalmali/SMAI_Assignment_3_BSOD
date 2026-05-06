import os
import json
import re
from typing import Dict, Any, List

STUDENT_DETAILS = ["student_name", "mother_name", "father_name", "dob", "school_name", "unique_id", "index_no", "board"]
SUBJECT_FIELDS = ["marks", "grade"]
COMPONENT_FIELDS = ["THEORY", "TOTAL"]

class MarksheetEvaluator:
    def __init__(self, gt_path: str, model_folders: Dict[str, str]):
        self.gt_path = gt_path
        self.model_folders = model_folders
        # Tracking: {model_name: {"student": [correct, total], "subjects": [correct, total]}}
        self.stats = {name: {"student": [0, 0], "subjects": [0, 0]} for name in model_folders}

    def normalize(self, val: Any) -> str:
        """Standardizes values for comparison: lowercase, no whitespace, handles floats."""
        if val is None: return ""
        # Convert numeric 96.0 to "96" to avoid float/string mismatch
        if isinstance(val, (int, float)):
            return str(int(val)) if val == int(val) else str(val)
        return str(val).strip().lower()

    def get_dynamic_value(self, flat_dict: Dict, target_key: str) -> str:
        """For Model 2: Searches flattened keys for a partial match to the target field."""
        target = target_key.lower().replace("_", "")
        for k, v in flat_dict.items():
            if target in k.lower().replace("_", ""):
                return self.normalize(v)
        return ""

    def flatten_json(self, y: Dict) -> Dict:
        """Recursively flattens nested JSON into a single-level dictionary."""
        out = {}
        def flatten(x, name=''):
            if type(x) is dict:
                for a in x: flatten(x[a], name + a + '_')
            elif type(x) is list:
                for i, a in enumerate(x): flatten(a, name + str(i) + '_')
            else:
                out[name[:-1]] = x
        flatten(y)
        return out

    def eval_student(self, gt: Dict, pred: Dict, is_dynamic: bool) -> List[int]:
        score, total = 0, 0
        pred_flat = self.flatten_json(pred) if is_dynamic else {}
        
        for field in STUDENT_DETAILS:
            gt_val = self.normalize(gt.get(field))
            if not gt_val: continue
            
            total += 1
            pred_val = self.get_dynamic_value(pred_flat, field) if is_dynamic else self.normalize(pred.get(field))
            if gt_val == pred_val:
                score += 1
        return [score, total]

    def eval_subjects(self, gt: Dict, pred: Dict, is_dynamic: bool) -> List[int]:
        score, total = 0, 0
        gt_subs = gt.get("subjects", [])
        pred_subs = pred.get("subjects", []) if not is_dynamic else []
        pred_flat = self.flatten_json(pred) if is_dynamic else {}

        for g_sub in gt_subs:
            sub_name = self.normalize(g_sub.get("subject", ""))
            # 1. Match subject in prediction
            p_sub = next((s for s in pred_subs if self.normalize(s.get("subject")) == sub_name), None)
            
            # 2. Check marks and grades
            for field in SUBJECT_FIELDS:
                total += 1
                gt_val = self.normalize(g_sub.get(field))
                if is_dynamic:
                    # Search for something like "english_marks" or "mathematics_grade"
                    p_val = self.get_dynamic_value(pred_flat, f"{sub_name}_{field}")
                else:
                    p_val = self.normalize(p_sub.get(field)) if p_sub else ""
                if gt_val == p_val: score += 1

            # 3. Check Components (Theory/Total)
            for comp in g_sub.get("components", []):
                total += 1
                comp_name = comp.get("name") # e.g., "THEORY"[cite: 1]
                gt_comp_val = self.normalize(comp.get("marks"))
                
                if is_dynamic:
                    p_comp_val = self.get_dynamic_value(pred_flat, f"{sub_name}_{comp_name}")
                else:
                    # Standard structure search
                    p_components = p_sub.get("components", []) if p_sub else []
                    p_comp = next((c for c in p_components if self.normalize(c.get("name")) == self.normalize(comp_name)), None)
                    p_comp_val = self.normalize(p_comp.get("marks")) if p_comp else ""
                
                if gt_comp_val == p_comp_val: score += 1
        
        return [score, total]

    def run(self):
        files = [f for f in os.listdir(self.gt_path) if f.endswith(".json")]
        
        for model_name, folder in self.model_folders.items():
            is_dyn = (model_name == "Rule-based")
            for filename in files:
                try:
                    with open(os.path.join(self.gt_path, filename), 'r') as f: gt_data = json.load(f)
                    with open(os.path.join(folder, filename), 'r') as f: pred_data = json.load(f)
                    
                    s_res = self.eval_student(gt_data, pred_data, is_dyn)
                    m_res = self.eval_subjects(gt_data, pred_data, is_dyn)
                    
                    self.stats[model_name]["student"][0] += s_res[0]
                    self.stats[model_name]["student"][1] += s_res[1]
                    self.stats[model_name]["subjects"][0] += m_res[0]
                    self.stats[model_name]["subjects"][1] += m_res[1]
                except FileNotFoundError:
                    continue

    def report(self):
        print(f"{'Model':<20} | {'Student Acc':<15} | {'Subject Acc':<15} | {'Overall Acc':<15}")
        print("-" * 75)
        for name, data in self.stats.items():
            s_acc = (data["student"][0] / data["student"][1] * 100) if data["student"][1] > 0 else 0
            m_acc = (data["subjects"][0] / data["subjects"][1] * 100) if data["subjects"][1] > 0 else 0
            overall = ((data["student"][0] + data["subjects"][0]) / (data["student"][1] + data["subjects"][1]) * 100)
            print(f"{name:<20} | {s_acc:>13.2f}% | {m_acc:>13.2f}% | {overall:>13.2f}%")




if __name__ == "__main__":
    folders = {
        "Pure-LLM": "./model_1_output",
        "Rule-based": "./model_2_output",
        "Section-based": "./model_3_output"
    }
    evaluator = MarksheetEvaluator("./ground_truth", folders)
    evaluator.run()
    evaluator.report()