import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
from os import listdir
from os.path import isfile, join
import re
import os


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
            #resource = comparison_path[comparison_path.rfind("_")+1:comparison_path.rfind(".")]
            match = re.search(r'\d+', comparison_path)
            if match:
                resource = match.group() + "Words"
            content_sim = float(content_code.split("%")[0].strip())/100  # Wir nehmen nur den Prozentsatz
            data.append({"name": filename, "modificationType": modificationType, "contentSim": content_sim, "resource": resource})

    # DataFrames für die verschiedenen Gruppen erstellen
    df = pd.DataFrame(data)
    return df
    

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
    color_map = {
        '16784Words': '#0072B2',
        '847Words': '#E69F00',
        '228Words': '#F0E442',
        '59Words': '#CC79A7'
    }

    return px.bar(
        df, 
        x='name', 
        y='contentSim', 
        color='resource', 
        barmode ='group',
        labels={
            'name': 'Modification',
            'contentSim': 'Content - Similarity',
            'resource': 'Text size:'
        },
        color_discrete_map=color_map,
        category_orders={'resource':['16784Words', '847Words', '228Words', '59Words']}
        
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

def rename_name_column(name):
    return name.split('Manipulation_')[1].split('_')[0] + '.txt'

def buildDiagram(path):
    df = fromMarkdownToDataFrame(path)
    print(df)
    # df = main_df[f"df_word"]
    # df = sortDataFrame(df)
    # df = dataFrameGroupByModificationType(df)
    # group_df = df['add']
    title = "Manipulation_modify_number_year"  
    df['name'] =  df['name'].apply(rename_name_column)
    fig = create_Bar_Diagram(df)
    updateAxes(fig)
    updateLayout(fig, title)
    createJPEG(fig, title.split("Manipulation_")[1]+"_content-code", path)    
    fig.show()

def main():
    path = "Desktop/bachelorarbeit/Testdaten/Ergebnisse/text/word/test"
    buildDiagram(path)

if __name__ == "__main__":
    main()