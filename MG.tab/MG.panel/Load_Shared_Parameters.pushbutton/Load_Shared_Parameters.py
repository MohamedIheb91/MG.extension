#! python3
__title__ = "Load Shared\nParameters"
__author__ = "Mohamed Iheb Gherissi"

# BOILERPLATE
import System
import clr
import os

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

## caricamento librerie per WPF
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

from System.Windows import Window, LogicalTreeHelper
from System.Windows.Markup import XamlReader
from System.Windows.Forms import OpenFileDialog
from System.Windows.Controls import CheckBox
from System.Windows.Media import Brushes


uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document # oggetto documento

# Gruppi di parametri?
## da ispezionare meglio la possibilità di rendere questo gruppo
## un gruppo estraibile da revit API

GRUPPI_UTILI = [
  "IdentityData", "Constraints", "Construction", "Geometry",
  "General", "Graphics", "Materials", "Mechanical", "Electrical",
  "Plumbing", "Structural", "Phasing", "Text", "Data", "Area",
  "AnalyticalModel", "FireProtection", "LifeSafety"
]


# 00 - Classe per salvare info base categorie
class Categoria:
    def __init__(self, cat):
        self.name = cat.Name
        self.type = cat.CategoryType
        self.id = cat.Id
        self.allows_bound = cat.AllowsBoundParameters
    def __repr__(self):
        return f"{self.name} of type {self.type} and ID: {self.id}"


# 01 - selezione dei category type
categorie = list()
tipi_categorie = set()
for bic in System.Enum.GetValues(BuiltInCategory):
    try:
        cat = Category.GetCategory(doc, bic)
        if cat is not None:
            categorie.append(Categoria(cat))
            tipi_categorie.add(Categoria(cat).type)
        
    except:
        pass

class SharedParameterWindows(Window):
    def __init__(self):
        xaml_path = os.path.join(os.path.dirname(__file__), "MainWindow.xaml")
        # Lettura file degli shared parameters
        with open(xaml_path, "r", encoding="utf-8-sig") as f:
            xaml = f.read()
        win = XamlReader.Parse(xaml)

        # Caricamento del percorso del file
        txt_file_path = LogicalTreeHelper.FindLogicalNode(win, "txtFilePath")
        sp_path = doc.Application.SharedParametersFilename # estrazione file già caricato
        if sp_path and os.path.exists(sp_path):
            txt_file_path.Text = sp_path
        else:
            txt_file_path.Text = "Nessun file caricato"

        def browse_file(sender, args):
            dialog = OpenFileDialog()
            dialog.Filter = "Shared Parameter File (*.txt)|*.txt"
            if dialog.ShowDialog():
                txt_file_path.Text = dialog.FileName

        btn_browse = LogicalTreeHelper.FindLogicalNode(win, "btnBrowse")
        btn_browse.Click += browse_file

        # Caricamento parametri dal file

        list_parameters = LogicalTreeHelper.FindLogicalNode(win, "listParameters")

        existing_guids = set()
        it = doc.ParameterBindings.ForwardIterator()
        it.Reset()
        while it.MoveNext():
            defn = it.Key
            elem = doc.GetElement(defn.Id)
            if isinstance(elem, SharedParameterElement):
                existing_guids.add(elem.GuidValue)

        # Costruisco il dizionario delle categorie già che hanno il parametro
        existing_categories = {}
        it2 = doc.ParameterBindings.ForwardIterator()
        it2.Reset()
        while it2.MoveNext():
            defn = it2.Key
            elem = doc.GetElement(defn.Id)
            if isinstance(elem, SharedParameterElement):
                binding = it2.Current
                cat_names = set(c.Name for c in binding.Categories)
                existing_categories[elem.GuidValue] = cat_names
        
        def_file = doc.Application.OpenSharedParameterFile()
        if def_file is not None:
            for group in def_file.Groups:
                for definition in group.Definitions:
                    cb_param = CheckBox()
                    cb_param.Content = definition.Name
                    if definition.GUID in existing_guids:
                        cb_param.Foreground = Brushes.Gray
                    list_parameters.Items.Add(cb_param)
        
        def on_param_selected(sender, args):
            selected_cb = list_parameters.SelectedItem
            if selected_cb is None:
                print("nessun elemento selezionato")
                return
            param_name = selected_cb.Content
            print("parametro selezionato:", param_name)
            guid = next((d.GUID for g in def_file.Groups for d in g.Definitions if d.Name == param_name), None)
            print("guid trovato", guid)
            print("guid in existing_categories", guid in existing_categories)
            if guid is None or guid not in existing_categories:
                return
            cats_to_check = existing_categories[guid]
            print("categorie da spuntare", cats_to_check)
            print("categirie nella lista:", [cb.Content for cb in list_categiries.Items])
            for cb in list_categories.Items:
                if cb.Content in cats_to_check:
                    cb.IsChecked = True
        list_parameters.SelectionChanged += on_param_selected
                
        # Category types
        list_category_types = LogicalTreeHelper.FindLogicalNode(win, "listCategoryTypes")
        def on_type_checked(sender, args):
            selected_types = [cb.Content for cb in list_category_types.Items if cb.IsChecked]
            list_categories = LogicalTreeHelper.FindLogicalNode(win, "listCategories")
            list_categories.Items.Clear()
            for cat in categorie:
                if str(cat.type) in selected_types and cat.allows_bound:
                    cb_cat = CheckBox()
                    cb_cat.Content = cat.name
                    list_categories.Items.Add(cb_cat)

        for tipo in tipi_categorie:
            cb = CheckBox()
            cb.Content = str(tipo)
            cb.Checked += on_type_checked
            cb.Unchecked += on_type_checked
            list_category_types.Items.Add(cb)

        # Chack All / check None categories
        list_categories = LogicalTreeHelper.FindLogicalNode(win, "listCategories")
        btn_check_all = LogicalTreeHelper.FindLogicalNode(win, "btnCheckAll")
        btn_check_none = LogicalTreeHelper.FindLogicalNode(win, "btnCheckNone")

        def check_all(sender, args):
            for cb in list_categories.Items:
                cb.IsChecked = True
        def check_none(sender, args):
            for cb in list_categories.Items:
                cb.IsChecked = False

        btn_check_all.Click += check_all
        btn_check_none.Click += check_none


        # Quarta colonna
        rb_istance = LogicalTreeHelper.FindLogicalNode(win, "rbInstance")
        rb_type = LogicalTreeHelper.FindLogicalNode(win, "rbType")
        chk_varies = LogicalTreeHelper.FindLogicalNode(win, "chkVariesByGroup")

        rb_istance.IsChecked = True
        chk_varies.IsChecked = True
        def on_binding_changed(sender, args):
            chk_varies.IsEnabled = rb_istance.IsChecked

        rb_istance.Checked += on_binding_changed
        rb_type.Checked += on_binding_changed

        # popolamento dei parameter group
        cmb_group = LogicalTreeHelper.FindLogicalNode(win, "cmbGroupUnder")
        group_ids = {}
        for name in GRUPPI_UTILI:
            val = getattr(GroupTypeId, name, None)
            if val:
              label = LabelUtils.GetLabelForGroup(val)
              group_ids[label] = val
              cmb_group.Items.Add(label)
        cmb_group.SelectedIndex = 0

        # Pulsante Applica

        btn_apply = LogicalTreeHelper.FindLogicalNode(win, "btnApply")
        def apply(sender, args):
            # parametri selezionati
            selected_params = [cb.Content for cb in list_parameters.Items if cb.IsChecked]

            # categorie selezionate
            selected_cats = [cb.Content for cb in list_categories.Items if cb.IsChecked]

            # opzioni
            is_istance = rb_istance.IsChecked
            varies = chk_varies.IsChecked
            group_label = cmb_group.SelectedItem
            group_id = group_ids.get(group_label)

            if not selected_params or not selected_cats or not group_id:
                print("Seleziona almeno un parametro, una categoria e un gruppo.")
                return

            t = Transaction(doc, "Inserimento Shared Parameters")
            t.Start()
            try:
                for param_name in selected_params:
                    definition = None
                    for group in def_file.Groups:
                        for d in group.Definitions:
                            if d.Name == param_name:
                                definition = d
                                break
                        
                    if definition is None:
                        continue
                    cat_set = CategorySet()
                    for cat_name in selected_cats:
                      for cat in categorie:
                          if cat.name == cat_name:
                              revit_cat = Category.GetCategory(doc, cat.id)
                              if revit_cat is not None and revit_cat.AllowsBoundParameters:
                                  cat_set.Insert(revit_cat)
                              break
                    binding = InstanceBinding(cat_set) if is_istance else TypeBinding(cat_set)
                    doc.ParameterBindings.Insert(definition, binding, group_id)
                t.Commit()
                print("parameteri inseriti con successo.")
            except Exception as e:
                t.RollBack()
                print("Errore:",e)
        btn_apply.Click += apply
              
        # Fondo della classe
        win.ShowDialog()



# Esecuzione
SharedParameterWindows()
