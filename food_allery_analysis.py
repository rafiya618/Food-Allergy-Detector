import csv
from collections import defaultdict, Counter
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from datetime import datetime

# --- Data Loading Functions ---

def load_foods_allergies(filepath):
    foods = {}
    ingredients_map = {}
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dish = row['dish_name'].strip()
            # Changed 'allergies' to 'allergens'
            allergens = [a.strip().lower() for a in row['allergens'].split(',') if a.strip()]
            foods[dish] = allergens
            ingredients = [i.strip().lower() for i in row['main_ingredients'].split(',') if i.strip()]
            ingredients_map[dish] = ingredients
    return foods, ingredients_map

def load_allergies_diseases(filepath):
    allergies = {}
    all_issues = set()
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            allergy = row['Allergy'].strip().lower()
            issues = [i.strip() for i in row['Related_Diseases_or_Issues'].split(';') if i.strip()]
            allergies[allergy] = [i.lower() for i in issues]
            all_issues.update([i.lower() for i in issues])
    return allergies, sorted(all_issues)

# --- Feedback System ---

class FeedbackSystem:
    def __init__(self, feedback_file='feedback.json'):
        self.feedback_file = feedback_file
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'w') as f:
                json.dump([], f)
        self.model_adjustments_file = 'model_adjustments.json'
        if not os.path.exists(self.model_adjustments_file):
            with open(self.model_adjustments_file, 'w') as f:
                json.dump({}, f)

    def save_feedback(self, user_feedback, analysis_results):
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'feedback': user_feedback,
            'results': analysis_results
        }
        with open(self.feedback_file, 'r+') as f:
            data = json.load(f)
            data.append(feedback_entry)
            f.seek(0)
            json.dump(data, f, indent=2)
        # Use feedback to improve model
        self.improve_model(user_feedback, analysis_results)

    def improve_model(self, user_feedback, analysis_results):
        # user_feedback['confirmed_ingredient'] is the ingredient user confirms as culprit
        confirmed = user_feedback.get('confirmed_ingredient')
        if not confirmed:
            return
        # Track confirmed ingredient as culprit
        with open(self.model_adjustments_file, 'r+') as f:
            data = json.load(f)
            data[confirmed] = data.get(confirmed, 0) + 1
            f.seek(0)
            json.dump(data, f, indent=2)

    def get_feedback_stats(self):
        with open(self.feedback_file, 'r') as f:
            data = json.load(f)
        return {
            'total_feedback': len(data),
            'recent_feedback': data[-5:] if len(data) > 5 else data
        }

    def get_model_adjustments(self):
        with open(self.model_adjustments_file, 'r') as f:
            return json.load(f)

# --- Main Application ---

class FoodAllergyApp:
    def __init__(self, root, foods_dict, ingredients_map, all_issues):
        self.root = root
        self.foods_dict = foods_dict
        self.ingredients_map = ingredients_map
        self.all_issues = all_issues
        self.food_names = sorted(list(foods_dict.keys()))  # Sort food names ascending
        self.day = 1
        self.meal_idx = 0
        self.meals = ['Breakfast', 'Lunch', 'Dinner']
        self.daily_data = []
        self.current_day_entry = {'foods': [], 'issues': []}
        self.selected_food = tk.StringVar()
        self.selected_issues = []
        self.user_issues = []
        self.feedback_system = FeedbackSystem()
        self.setup_ui()
        self.show_welcome_screen()

    def setup_ui(self):
        self.root.title("Food Allergy Analyzer")
        self.root.geometry("800x600")
        self.root.configure(bg="#f5f5f5")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure('TFrame', background="#f5f5f5")
        self.style.configure('TLabel', background="#f5f5f5", font=('Arial', 12))
        self.style.configure('TButton', font=('Arial', 12), padding=5)
        self.style.configure('Title.TLabel', font=('Arial', 18, 'bold'), foreground="#2c3e50")
        
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New Analysis", command=self.reset_analysis)
        self.file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status("Ready")

    def show_welcome_screen(self):
        self.clear_main_frame()
        
        welcome_frame = ttk.Frame(self.main_frame)
        welcome_frame.pack(expand=True, pady=50)
        
        ttk.Label(welcome_frame, text="Welcome to Food Allergy Analyzer", style='Title.TLabel').pack(pady=20)
        
        ttk.Label(welcome_frame, text="Track your meals and symptoms to identify potential food allergies", 
                 wraplength=400, justify=tk.CENTER).pack(pady=10)
        
        ttk.Label(welcome_frame, text="How it works:").pack(pady=5)
        
        steps = [
            "1. Record your meals for 4 days (breakfast, lunch, dinner)",
            "2. Report any health issues you experience",
            "3. Get analysis of potential food culprits",
            "4. Receive alternative food suggestions"
        ]
        
        for step in steps:
            ttk.Label(welcome_frame, text=step, justify=tk.LEFT).pack(anchor=tk.W, padx=20)
        
        start_btn = ttk.Button(welcome_frame, text="Start Analysis", command=self.ask_issues_first)
        start_btn.pack(pady=30, ipadx=20, ipady=10)
        
        feedback_btn = ttk.Button(welcome_frame, text="View Feedback", command=self.show_feedback_stats)
        feedback_btn.pack(pady=10, ipadx=20, ipady=5)

    def ask_issues_first(self):
        self.clear_main_frame()
        ttk.Label(self.main_frame, text="Select health issues you want to track:", style='Title.TLabel').pack(pady=20)
        issues_frame = ttk.Frame(self.main_frame)
        issues_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scroll_frame = ttk.Frame(issues_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.issues_listbox = tk.Listbox(scroll_frame, selectmode=tk.MULTIPLE, 
                                         yscrollcommand=scrollbar.set, height=10,
                                         font=('Arial', 11), background="white")
        for issue in [i.capitalize() for i in self.all_issues]:
            self.issues_listbox.insert(tk.END, issue)
        self.issues_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.issues_listbox.yview)
        
        btn_frame = ttk.Frame(issues_frame)
        btn_frame.pack(pady=10)
        
        next_btn = ttk.Button(btn_frame, text="Next", command=self.save_issues_and_start_meal)
        next_btn.pack(side=tk.LEFT, padx=5)

    def save_issues_and_start_meal(self):
        selected_indices = self.issues_listbox.curselection()
        self.user_issues = [self.issues_listbox.get(i).lower() for i in selected_indices]
        if not self.user_issues:
            messagebox.showwarning("Input Error", "Please select at least one issue to track.")
            return
        self.day = 1
        self.meal_idx = 0
        self.daily_data = []
        self.current_day_entry = {'foods': [], 'issues': []}
        self.setup_food_selection_ui()

    def setup_food_selection_ui(self):
        self.clear_main_frame()
        self.title_label = ttk.Label(self.main_frame, text="Food Allergy Analyzer", style='Title.TLabel')
        self.title_label.pack(pady=10)
        self.day_label = ttk.Label(self.main_frame, text=f"Day {self.day} - {self.meals[self.meal_idx]}", 
                                 font=('Arial', 14, 'bold'))
        self.day_label.pack(pady=5)
        # Food selection frame
        food_frame = ttk.Frame(self.main_frame)
        food_frame.pack(pady=10)
        ttk.Label(food_frame, text="Select food:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        # Use sorted food names
        self.food_combo = ttk.Combobox(food_frame, values=self.food_names, textvariable=self.selected_food, 
                                     state="readonly", width=40)
        self.food_combo.grid(row=0, column=1, padx=5, pady=5)
        self.next_btn = ttk.Button(food_frame, text="Next", command=self.next_meal)
        self.next_btn.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Progress indicator
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(pady=20)
        
        for i in range(4):
            day_color = "#3498db" if i+1 == self.day else "#bdc3c7"
            ttk.Label(self.progress_frame, text=f"Day {i+1}", 
                     background=day_color, foreground="white", 
                     padding=5, relief=tk.RAISED).grid(row=0, column=i, padx=5)

    def next_meal(self):
        food = self.selected_food.get()
        if not food:
            messagebox.showwarning("Input Error", "Please select a food for this meal.")
            return
        self.current_day_entry['foods'].append(food)
        self.selected_food.set('')
        self.food_combo.set('')
        self.meal_idx += 1
        if self.meal_idx < 3:
            self.day_label.config(text=f"Day {self.day} - {self.meals[self.meal_idx]}")
        else:
            self.finish_day()

    def finish_day(self):
        self.current_day_entry['issues'] = list(self.user_issues)
        self.daily_data.append(self.current_day_entry.copy())
        self.current_day_entry = {'foods': [], 'issues': []}
        self.meal_idx = 0
        if self.day < 4:
            self.day += 1
            self.setup_food_selection_ui()
        else:
            self.analyze_and_show_results()

    def analyze_and_show_results(self):
        self.clear_main_frame()
        # Ingredient-level analysis
        ingredient_issue_map = defaultdict(int)
        ingredient_food_map = defaultdict(set)
        for entry in self.daily_data:
            for food in entry['foods']:
                allergies = self.foods_dict.get(food, [])
                for allergy in allergies:
                    ingredient_issue_map[allergy] += sum(1 for issue in entry['issues'] if issue in allergies_dict.get(allergy, []))
                    ingredient_food_map[allergy].add(food)
        # Adjust with user feedback history (model improvement)
        adjustments = self.feedback_system.get_model_adjustments()
        for ing, count in adjustments.items():
            ingredient_issue_map[ing] += count  # boost score for confirmed culprits

        max_score = max(ingredient_issue_map.values(), default=0)
        probable_ingredients = [ing for ing, score in ingredient_issue_map.items() if score == max_score and score > 0]
        culprit_foods = set()
        for ing in probable_ingredients:
            culprit_foods.update(ingredient_food_map[ing])

        # --- Save analysis results for feedback ---
        self.analysis_results = {
            'ingredient_issue_map': dict(ingredient_issue_map),
            'probable_ingredients': probable_ingredients,
            'culprit_foods': list(culprit_foods)
        }

        # Results display
        ttk.Label(self.main_frame, text="Analysis Results", style='Title.TLabel').pack(pady=10)
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Summary")
        summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, font=('Arial', 11))
        summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        summary_text.insert(tk.END, "Culprit ingredient(s) likely causing your issues:\n")
        if probable_ingredients:
            for ing in probable_ingredients:
                summary_text.insert(tk.END, f"  {ing.title()} (in foods: {', '.join(f.title() for f in ingredient_food_map[ing])})\n")
            summary_text.insert(tk.END, "\nFoods to avoid:\n")
            for food in culprit_foods:
                summary_text.insert(tk.END, f"  {food.title()} (contains: {', '.join(self.foods_dict[food]).title()})\n")
            # Suggest alternatives: foods that do not contain any culprit ingredient
            alternative_foods = [food for food, ings in self.foods_dict.items() if not set(probable_ingredients).intersection(ings)]
            summary_text.insert(tk.END, "\nSuggested alternative foods:\n")
            if alternative_foods:
                for food in alternative_foods[:10]:
                    summary_text.insert(tk.END, f"  {food.title()}\n")
            else:
                summary_text.insert(tk.END, "  No clear alternatives found.\n")
        else:
            summary_text.insert(tk.END, "No clear culprit ingredient identified. Try collecting more data.\n")
        summary_text.config(state=tk.DISABLED)
        
        # Details tab
        details_frame = ttk.Frame(notebook)
        notebook.add(details_frame, text="Details")
        
        details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, font=('Arial', 11))
        details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        details_text.insert(tk.END, "Daily Breakdown:\n\n")
        for day, entry in enumerate(self.daily_data, 1):
            details_text.insert(tk.END, f"Day {day}:\n")
            details_text.insert(tk.END, f"  Foods: {', '.join(f.title() for f in entry['foods'])}\n")
            if entry['issues']:
                details_text.insert(tk.END, f"  Issues: {', '.join(i.title() for i in entry['issues'])}\n")
            details_text.insert(tk.END, "\n")
        
        details_text.config(state=tk.DISABLED)
        
        # Feedback tab
        feedback_frame = ttk.Frame(notebook)
        notebook.add(feedback_frame, text="Feedback")
        
        ttk.Label(feedback_frame, text="Which ingredient do you think actually caused your issue?", font=('Arial', 12)).pack(pady=10)
        # Ingredient options: show all ingredients that appeared in user's foods
        all_ingredients = set()
        for entry in self.daily_data:
            for food in entry['foods']:
                all_ingredients.update(self.foods_dict.get(food, []))
        all_ingredients = sorted(all_ingredients)
        self.feedback_ingredient_var = tk.StringVar()
        ingredient_combo = ttk.Combobox(feedback_frame, values=[i.title() for i in all_ingredients], textvariable=self.feedback_ingredient_var, state="readonly", width=30)
        ingredient_combo.pack(pady=5)
        
        ttk.Label(feedback_frame, text="How accurate were these results?").pack(pady=10)
        
        self.feedback_var = tk.IntVar(value=3)
        feedback_scale = ttk.Scale(feedback_frame, from_=1, to=5, variable=self.feedback_var, 
                                 command=lambda v: self.update_feedback_label(int(float(v))))
        feedback_scale.pack(fill=tk.X, padx=20, pady=5)
        
        self.feedback_label = ttk.Label(feedback_frame, text="Neutral (3)")
        self.feedback_label.pack()
        
        ttk.Label(feedback_frame, text="Additional comments:").pack(pady=5)
        
        self.comments_text = scrolledtext.ScrolledText(feedback_frame, wrap=tk.WORD, height=5, font=('Arial', 11))
        self.comments_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        submit_btn = ttk.Button(feedback_frame, text="Submit Feedback", command=self.submit_feedback)
        submit_btn.pack(pady=10)
        
        # Action buttons
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="New Analysis", command=self.reset_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT, padx=5)

    def update_feedback_label(self, value):
        labels = {
            1: "Very Inaccurate (1)",
            2: "Somewhat Inaccurate (2)",
            3: "Neutral (3)",
            4: "Somewhat Accurate (4)",
            5: "Very Accurate (5)"
        }
        self.feedback_label.config(text=labels.get(value, "Neutral (3)"))

    def submit_feedback(self):
        confirmed_ingredient = self.feedback_ingredient_var.get().lower() if self.feedback_ingredient_var.get() else ""
        feedback = {
            'rating': self.feedback_var.get(),
            'comments': self.comments_text.get("1.0", tk.END).strip(),
            'timestamp': datetime.now().isoformat(),
            'confirmed_ingredient': confirmed_ingredient
        }
        self.feedback_system.save_feedback(feedback, self.analysis_results)
        messagebox.showinfo("Thank You", "Your feedback has been submitted and will help improve future analysis!")
        self.show_welcome_screen()

    def show_feedback_stats(self):
        stats = self.feedback_system.get_feedback_stats()
        
        feedback_window = tk.Toplevel(self.root)
        feedback_window.title("Feedback Statistics")
        feedback_window.geometry("500x400")
        
        ttk.Label(feedback_window, text="Feedback Statistics", style='Title.TLabel').pack(pady=10)
        
        ttk.Label(feedback_window, text=f"Total feedback submissions: {stats['total_feedback']}").pack(pady=5)
        
        if stats['recent_feedback']:
            ttk.Label(feedback_window, text="Recent feedback:").pack(pady=5)
            
            text_area = scrolledtext.ScrolledText(feedback_window, wrap=tk.WORD)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            for feedback in stats['recent_feedback']:
                text_area.insert(tk.END, f"{feedback['timestamp']}\n")
                text_area.insert(tk.END, f"Rating: {feedback['feedback']['rating']}/5\n")
                if feedback['feedback']['comments']:
                    text_area.insert(tk.END, f"Comments: {feedback['feedback']['comments']}\n")
                text_area.insert(tk.END, "-"*50 + "\n")
            
            text_area.config(state=tk.DISABLED)
        
        ttk.Button(feedback_window, text="Close", command=feedback_window.destroy).pack(pady=10)

    def show_about(self):
        messagebox.showinfo("About", "Food Allergy Analyzer\nVersion 1.0\n\nTrack your meals and symptoms to identify potential food allergies.")

    def reset_analysis(self):
        self.day = 1
        self.meal_idx = 0
        self.daily_data = []
        self.current_day_entry = {'foods': [], 'issues': []}
        self.selected_food.set('')
        self.selected_issues = []
        self.show_welcome_screen()

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def update_status(self, message):
        self.status_var.set(message)

# --- Analysis Functions ---

def map_foods_to_allergies(daily_data, foods_dict):
    for entry in daily_data:
        entry['allergies'] = []
        for food in entry['foods']:
            entry['allergies'].extend(foods_dict.get(food, []))
    return daily_data

def map_allergies_to_issues(daily_data, allergies_dict):
    for entry in daily_data:
        entry['possible_issues'] = []
        for allergy in entry['allergies']:
            entry['possible_issues'].extend(allergies_dict.get(allergy, []))
    return daily_data

def analyze_patterns(daily_data):
    food_counter = Counter()
    allergy_counter = Counter()
    issue_counter = Counter()
    food_issue_map = defaultdict(list)

    for entry in daily_data:
        for food in entry['foods']:
            food_counter[food] += 1
        for allergy in entry['allergies']:
            allergy_counter[allergy] += 1
        for issue in entry['issues']:
            issue_counter[issue] += 1
        for food in entry['foods']:
            for issue in entry['issues']:
                food_issue_map[food].append(issue)

    return food_counter, allergy_counter, issue_counter, food_issue_map

def find_probable_culprits(food_issue_map, foods_dict, allergies_dict, daily_data):
    culprit_scores = {}
    for food, issues in food_issue_map.items():
        allergies = foods_dict.get(food, [])
        possible_issues = set()
        for allergy in allergies:
            possible_issues.update(allergies_dict.get(allergy, []))
        match_count = sum(1 for issue in issues if issue in possible_issues)
        culprit_scores[food] = match_count

    max_score = max(culprit_scores.values(), default=0)
    probable_culprits = [food for food, score in culprit_scores.items() if score == max_score and score > 0]
    return probable_culprits, culprit_scores

def suggest_alternative(culprit, foods_dict):
    culprit_allergies = set(foods_dict.get(culprit, []))
    for food, allergies in foods_dict.items():
        if food != culprit and not culprit_allergies.intersection(allergies):
            return food
    return None

# --- Main Function ---

def main():
    try:
        foods_dict, ingredients_map = load_foods_allergies('foods_allergies.csv')
        global allergies_dict
        allergies_dict, all_issues = load_allergies_diseases('allergies_diseases.csv')
    except Exception as e:
        print("Error loading CSV files:", e)
        return

    root = tk.Tk()
    app = FoodAllergyApp(root, foods_dict, ingredients_map, all_issues)
    root.mainloop()

if __name__ == "__main__":
    main()