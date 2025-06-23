from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.properties import StringProperty
import json
import os
from datetime import datetime

PASSWORD_FILE = "user_data.json"

class SmartPantryApp(App):
    current_category = StringProperty("")
    selected_item = StringProperty("")
    inventory_screen = None

    def build(self):
        from kivy.lang import Builder
        Builder.load_file("SmartPantry.kv")

        with open('recipes.json', 'r', encoding='utf-8') as f:
            self.recipes = json.load(f)

        self.items = {
            'fruits_vegetables': [],
            'grains': [],
            'non_veg': [],
            'dairy': [],
            'others': []
        }

        sm = ScreenManager()
        sm.add_widget(CreatePasswordScreen(name='create_password'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(ResetPasswordScreen(name='reset_password'))
        sm.add_widget(CategoryScreen(name='category'))
        sm.add_widget(FruitsVegetablesScreen(name='fruits_vegetables'))
        sm.add_widget(GrainsScreen(name='grains'))
        sm.add_widget(NonVegScreen(name='non_veg'))
        sm.add_widget(DairyScreen(name='dairy'))
        sm.add_widget(OthersScreen(name='others'))
        sm.add_widget(RecipeListScreen(name='recipe_list'))
        sm.add_widget(RecipeScreen(name='recipe_detail'))

        if os.path.exists(PASSWORD_FILE):
            sm.current = 'login'
        else:
            sm.current = 'create_password'

        return sm

    def save_password(self):
        screen = self.root.get_screen('create_password')
        name = screen.ids.name_input.text
        password = screen.ids.password_input.text
        if name and password:
            with open(PASSWORD_FILE, 'w') as f:
                json.dump({'name': name, 'password': password}, f)
            self.root.current = 'login'
        else:
            screen.ids.status_label.text = "Both fields are required."

    def submit_info(self):
        screen = self.root.get_screen('login')
        name = screen.ids.name_input.text
        password = screen.ids.password_input.text
        if os.path.exists(PASSWORD_FILE):
            with open(PASSWORD_FILE, 'r') as f:
                data = json.load(f)
            if data['name'] == name and data['password'] == password:
                self.root.current = 'category'
            else:
                screen.ids.login_status.text = "Invalid credentials."

    def reset_password(self):
        screen = self.root.get_screen('reset_password')
        name = screen.ids.name_input.text
        new_password = screen.ids.new_password_input.text
        if os.path.exists(PASSWORD_FILE):
            with open(PASSWORD_FILE, 'r') as f:
                data = json.load(f)
            if data['name'] == name:
                data['password'] = new_password
                with open(PASSWORD_FILE, 'w') as f:
                    json.dump(data, f)
                screen.ids.status_label.text = "Password reset successful."
                self.root.current = 'login'
            else:
                screen.ids.status_label.text = "Name not found."

    def open_category(self, category):
        self.current_category = category
        screen = self.root.get_screen(category)
        screen.ids.category_label.text = f"{category.replace('_', ' ').title()} Inventory"
        screen.ids.item_input.text = ""
        screen.ids.mfg_input.text = ""
        screen.ids.exp_input.text = ""
        screen.ids.inventory_box.clear_widgets()
        screen.ids.status_label.text = ""
        self.root.current = category

    def add_item(self):
        category = self.current_category
        screen = self.root.get_screen(category)
        name = screen.ids.item_input.text
        mfg = screen.ids.mfg_input.text
        exp = screen.ids.exp_input.text
        if name and mfg and exp:
            try:
                exp_date = datetime.strptime(exp, "%d/%m/%Y")
                expired = exp_date < datetime.now()
                self.items[category].append((name, mfg, exp, expired))
                screen.ids.status_label.text = "Item added."
                screen.ids.item_input.text = ""
                screen.ids.mfg_input.text = ""
                screen.ids.exp_input.text = ""
            except ValueError:
                screen.ids.status_label.text = "Invalid date format."
        else:
            screen.ids.status_label.text = "Fill all fields."

    def show_inventory(self):
        category = self.current_category
        screen = self.root.get_screen(category)
        self.inventory_screen = screen
        screen.ids.inventory_box.clear_widgets()
        for item in self.items[category]:
            box = BoxLayout(size_hint_y=None, height=60, spacing=10)
            label = Label(
                text=f"{item[0]}, Exp: {item[2]}, {'Expired' if item[3] else 'Fresh'}",
                color=(0, 0, 0, 1)  # Black text
            )
            button_box = BoxLayout(orientation='horizontal', size_hint_x=None, width=180, spacing=5)
            remove_btn = Button(text="Remove", size_hint_x=None, width=85)
            remove_btn.bind(on_press=lambda x, i=item: self.remove_item(i))
            suggest_btn = Button(text="Suggest", size_hint_x=None, width=85)
            suggest_btn.bind(on_press=lambda x, i=item: self.suggest_recipe(i))
            button_box.add_widget(remove_btn)
            button_box.add_widget(suggest_btn)
            box.add_widget(label)
            box.add_widget(button_box)
            screen.ids.inventory_box.add_widget(box)

    def remove_item(self, item):
        category = self.current_category
        if item in self.items[category]:
            self.items[category].remove(item)
            self.show_inventory()

    def suggest_recipe(self, item):
        self.selected_item = item[0].lower()
        recipe_screen = self.root.get_screen('recipe_list')
        recipe_screen.ids.recipe_list.clear_widgets()

        self.matched_recipes = [recipe for recipe in self.recipes if self.selected_item in [i.lower() for i in recipe['ingredients']]]

        for recipe in self.matched_recipes:
            btn = Button(text=recipe['title'], size_hint_y=None, height=40)
            btn.bind(on_press=lambda x, r=recipe: self.show_recipe_details(r))
            recipe_screen.ids.recipe_list.add_widget(btn)

        self.root.current = 'recipe_list'

    def show_recipe_details(self, recipe):
        recipe_screen = self.root.get_screen('recipe_detail')
        recipe_screen.ids.recipe_title.text = recipe['title']
        recipe_screen.ids.recipe_ingredients.text = "\n".join(recipe['ingredients'])
        recipe_screen.ids.recipe_instructions.text = recipe['instructions']
        self.root.current = 'recipe_detail'

    def go_back_to_inventory(self):
        if self.inventory_screen:
            self.root.current = self.inventory_screen.name

class CreatePasswordScreen(Screen): pass
class LoginScreen(Screen): pass
class ResetPasswordScreen(Screen): pass
class CategoryScreen(Screen): pass
class CategoryEntryScreen(Screen): pass
class FruitsVegetablesScreen(CategoryEntryScreen): pass
class GrainsScreen(CategoryEntryScreen): pass
class NonVegScreen(CategoryEntryScreen): pass
class DairyScreen(CategoryEntryScreen): pass
class OthersScreen(CategoryEntryScreen): pass
class RecipeListScreen(Screen): pass
class RecipeScreen(Screen): pass

if __name__ == '__main__':
    SmartPantryApp().run()
