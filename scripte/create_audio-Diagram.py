import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
from os import listdir
from os.path import isfile, join
import re
import os

modificationTargets = ['word', 'sentence', 'textblock', 'page', 'Hz', 'all', 'faster', 'slower', 'stereo', 'datatype']

def fromMarkdownToDataFrame(path):
    comparison_files = [f for f in listdir(path) if isfile(join(path, f))]
    data = []

    for comparison_file in comparison_files:
        comparison_path = join(path, comparison_file)
        
        # Datei einlesen
        if os.path.exists(comparison_path):
            with open(comparison_path, "r") as file:
                lines = file.readlines()
        else:
            print(f"Die Datei {comparison_path} existiert nicht.")

        # Daten extrahieren (wir überspringen die ersten beiden Zeilen, da sie Header und Trennzeichen sind)
        
        for line in lines[4:]:
            columns = line.split("|")
            if len(columns) < 6:  # Zeilen überspringen, die nicht genug Spalten haben
                continue
            
            filename = columns[1].strip()
            modificationType = filename.split("_")[1]
            content_code = columns[3].strip() # 3 Für Semantic-Code; 4 für Content-Code
            resource = comparison_path[comparison_path.rfind("_")+1:comparison_path.rfind(".")]
            
            # Wir filtern nur Zeilen mit Dateinamen, die wir benötigen
            if re.search(r"page|textblock|sentence|word|Hz|all|faster|slower|stereo|datatype", filename):
                content_sim = float(content_code.split("%")[0].strip())/100  # Wir nehmen nur den Prozentsatz
                data.append({"name": filename, "modificationType": modificationType, "contentSim": content_sim, "resource": resource})

    # DataFrames für die verschiedenen Gruppen erstellen
    df_page = pd.DataFrame([entry for entry in data if "page" in entry['name']])
    df_textblock = pd.DataFrame([entry for entry in data if "textblock" in entry['name']])
    df_sentence = pd.DataFrame([entry for entry in data if "sentence" in entry['name']])
    df_word = pd.DataFrame([entry for entry in data if "word" in entry['name']])
    df_Hz = pd.DataFrame([entry for entry in data if "Hz" in entry['name']])
    df_all = pd.DataFrame([entry for entry in data if "all" in entry['name']])
    df_faster = pd.DataFrame([entry for entry in data if "faster" in entry['name']])
    df_slower = pd.DataFrame([entry for entry in data if "slower" in entry['name']])
    df_stereo = pd.DataFrame([entry for entry in data if "stereo" in entry['name']])
    df_datatype = pd.DataFrame([entry for entry in data if "datatype" in entry['name']])

    return{
        "df_page": df_page,
        "df_textblock": df_textblock,
        "df_sentence": df_sentence,
        "df_word": df_word,
        "df_Hz": df_Hz,
        "df_all": df_all,
        "df_faster": df_faster,
        "df_slower": df_slower,
        "df_stereo": df_stereo,
        "df_datatype": df_datatype
    }

def ProzentToDouble(value):
    return float(value)/100

def updateAxes(fig):
    fig.update_yaxes(
        range=[0.2, 1.02], 
        tickformat=".0%", 
        dtick=0.1
    )
    fig.update_xaxes(
        categoryorder='array',
        #categoryarray=['_1', '_5', '_10'],  # Reihenfolge der Kategorien
        tickangle=-45  # Optional: Labels schräg setzen, um Platz zu sparen
    )

def updateLayout(fig, title):
    fig.update_layout(
        title_text=title,
        width=500,
        height=500,
    )

def create_Bar_Diagram(df):
    return px.bar(
        df, 
        x='name', 
        y='contentSim', 
        color='resource', 
        barmode ='group',
        labels={
            'name': 'Modification',
            'contentSim': 'Content - Similarity',
            'resource': 'Audio length:'
        },
        color_discrete_map={
            '5m43s': '#0072B2',
            '1m26s': '#E69F00',
            '0m21s': '#F0E442'
        }
    )

def create_Line_Diagram(df):
    return px.line(
        df, 
        x='name', 
        y='contentSim', 
        color='resource', 
        markers=True,
        labels={
            'name': 'Modification',
            'contentSim': 'Similarity',
            'resource': 'Data size:'
        }
    )

def createJPEG(fig, name, savePlace):
    fig.write_image(f'{savePlace}/_{name}.jpeg')

def extract_number(filename):
    # Prüfen, ob "same" im Dateinamen enthalten ist
    if "all" in filename:
        return float('inf')  # Gibt einen extrem hohen Wert zurück
    elif "increased" in filename: 
        return 100
    elif "decreased" in filename:
        return 101
    # Andernfalls versuchen, eine Zahl zu extrahieren
    match = re.search(r'(\d+)', filename)
    if match:
        return int(match.group(1))
    return 0

def sortDataFrame(df):
    df['number'] = df['name'].apply(extract_number)
    df['number2'] = df['resource'].apply(extract_number)
    return df.sort_values(by=['number', 'number2'], ascending=[True, False]).drop(columns=['number', 'number2']) ##Sortiert noch nicht richtig 'number2'

def getTitle(df):
    targets = modificationTargets
    name = df['name']
    name = name[0].split(".")
    array = name[0].split("_")
    
    for i, elem in enumerate(array):
        if elem in targets:
            return "_".join(array[:i+1])
        
    return None

def rename_name_column(name):
    targets = modificationTargets
    # Durch die Liste der Zielbegriffe iterieren und den ersten finden
    for target in targets:
        if target in name:
            # Den neuen Namen im Format "target_#.txt" erstellen
            match = re.search(r'_(\d+)\.txt', name)
            if match:
                number = match.group(1)
                return f"{target}_{number}.txt"
            return f"{target}_{name.split(target, 1)[1]}"
    return name  # Falls kein Zielbegriff gefunden wird

def dataFrameGroupByModificationType(df):
    # DataFrame nach 'modificationType' gruppieren
    grouped = df.groupby('modificationType')
    # Dictionary, das die DataFrames für jede Gruppe speichert
    grouped_dfs = {}
    # Für jede Gruppe einen separaten DataFrame erstellen
    for modification_type, group in grouped:
        grouped_dfs[modification_type] = group.reset_index(drop=True)

    # for key, group_df in grouped_dfs.items():
    #     print(f"DataFrame for modification type: {key}")
    #     print(group_df)
    #     print("\n")

    return grouped_dfs

def buildDiagram(path):
    targets = modificationTargets
    main_df = fromMarkdownToDataFrame(path)

    df = main_df[f"df_word"]
    df = sortDataFrame(df)
    df = dataFrameGroupByModificationType(df)
    group_df = df['add']
    title = getTitle(group_df)
                
    group_df['name'] = group_df['name'].apply(rename_name_column)
    fig = create_Bar_Diagram(group_df)
    updateAxes(fig)
    updateLayout(fig, title)
    #createJPEG(fig, f"{group_name}_{target}", path)    
    fig.show()

def buildDiagrams(path):
    lineOrBar = input("line or bar: ")
    targets = modificationTargets

    main_df = fromMarkdownToDataFrame(path)
    
    for target in targets:
        df = main_df[f"df_{target}"]
        df = sortDataFrame(df)
        df = dataFrameGroupByModificationType(df)
        for group_name, group_df in df.items():
            group_df = df[group_name]
            title = getTitle(group_df)
                
            group_df['name'] = group_df['name'].apply(rename_name_column)
            try:
                if lineOrBar == "line":
                    fig = create_Line_Diagram(group_df)
                elif lineOrBar == "bar":
                    fig = create_Bar_Diagram(group_df)
                else:
                    raise Exception("Neustart")
            except Exception:
                print(f"schreiben Sie 'line' oder 'bar' um einen Diagrammtypen zu wählen.")
                buildDiagrams(path)
                return None
            updateAxes(fig)
            updateLayout(fig, title)
            createJPEG(fig, f"{group_name}_{target}_content-code", path)    
            #fig.show() 

def main():
    path = "Desktop/bachelorarbeit/twinspectTest/results/audio"
    buildDiagrams(path)

if __name__ == "__main__":
    main()