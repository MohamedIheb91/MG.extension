#! python3

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


uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document # oggetto documento

# Gruppi di parametri

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

        def_file = doc.Application.OpenSharedParameterFile()
        if def_file is not None:
            for group in def_file.Groups:
                for definition in group.Definitions:
                    cb_param = CheckBox()
                    cb_param.Content = definition.Name
                    list_parameters.Items.Add(cb_param)

        # Category types
        list_category_types = LogicalTreeHelper.FindLogicalNode(win, "listCategoryTypes")
        def on_type_checked(sender, args):
            selected_types = [cb.Content for cb in list_category_types.Items if cb.IsChecked]
            list_categories = LogicalTreeHelper.FindLogicalNode(win, "listCategories")
            list_categories.Items.Clear()
            for cat in categorie:
                if str(cat.type) in selected_types:
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
                # print("parameteri inseriti.")
            except Exception as e:
                t.RollBack()
                print("Errore:",e)
        btn_apply.Click += apply
              
        # Fondo della classe
        win.ShowDialog()



# Esecuzione
SharedParameterWindows()
