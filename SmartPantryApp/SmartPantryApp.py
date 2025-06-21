from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty
from datetime import datetime
import json
import os

PASSWORD_FILE = "user_data.json"

class InventoryCard(BoxLayout):
    item_text = StringProperty("")
    remove_callback = ObjectProperty(lambda *args: None)
    suggest_callback = ObjectProperty(lambda *args: None)

class SmartPantryApp(App):
    current_category = StringProperty("")

    def build(self):
        Builder.load_file("SmartPantry.kv")
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
        name = screen.ids.item_input.text.strip()
        mfg = screen.ids.mfg_input.text.strip()
        exp = screen.ids.exp_input.text.strip()

        if name and mfg and exp:
            try:
                exp_date = datetime.strptime(exp, "%d/%m/%Y").date()
                today = datetime.now().date()
                delta_days = (exp_date - today).days

                # Expiry label logic
                if delta_days < 0:
                    tag = "Expired"
                elif delta_days <= 7:
                    tag = "Expiry in a week"
                elif delta_days <= 30:
                    tag = "Expiry in 1 month"
                elif delta_days <= 60:
                    tag = "Expiry in 2 months"
                else:
                    months = delta_days // 30
                    tag = f"Expiry in {months} months"

                # Check for duplicate entry
                for item in self.items[category]:
                    if item[0] == name and item[2] == exp:
                        screen.ids.status_label.text = "Item already exists."
                        return

                # Add item and refresh view
                self.items[category].append((name, mfg, exp, tag))
                screen.ids.status_label.text = "Item added."
                screen.ids.item_input.text = ""
                screen.ids.mfg_input.text = ""
                screen.ids.exp_input.text = ""
                self.show_inventory()
            except ValueError:
                screen.ids.status_label.text = "Invalid date format (dd/mm/yyyy)."
        else:
            screen.ids.status_label.text = "Fill all fields."

    def show_inventory(self):
        category = self.current_category
        screen = self.root.get_screen(category)
        screen.ids.inventory_box.clear_widgets()

        for item in self.items[category]:
            item_name, mfg, exp, tag = item
            item_text = f"{item_name} | Exp: {exp} | {tag}"

            # Use default arguments in lambda to capture current item
            inv_card = InventoryCard(
                item_text=item_text,
                remove_callback=lambda i=item: self.remove_item(i),
                suggest_callback=lambda i=item: self.suggest_recipe(i)
            )
            screen.ids.inventory_box.add_widget(inv_card)

    def remove_item(self, item):
        category = self.current_category
        if item in self.items[category]:
            self.items[category].remove(item)
            self.show_inventory()

    def suggest_recipe(self, item):
        print(f"Suggesting recipe for {item[0]}...")

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

if __name__ == '__main__':
    SmartPantryApp().run()
