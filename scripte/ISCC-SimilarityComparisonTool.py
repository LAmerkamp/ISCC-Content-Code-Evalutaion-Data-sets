import sys
import os
import json
import mimetypes
import iscc_core as ic
import iscc_sdk as idk
import iscc_sct as sct
import iscc_sci as sci
from os import listdir
from os.path import isfile, join
from PIL import Image

def check_args(args):
    if len(args) != 3:
        print("Fehlende Argumente:\n1. Argument: /pfad/Datei der Originalen Datei\n2. Argument: /pfad des Verzeichnis mit den manipulierten Testdaten.")
        sys.exit(1)

    original_data_path, directory_data_path = args[1], args[2]

    if not os.path.exists(original_data_path):
        print(f"Die angegebene Datei '{original_data_path}' existiert nicht.")
        sys.exit(1)

    if not os.path.exists(directory_data_path):
        print(f"Der angegebene Pfad '{directory_data_path}' existiert nicht.")
        sys.exit(1)

    return original_data_path, directory_data_path

def generate_iscc_codes(datapath):
    meta_code = ic.gen_meta_code(name=os.path.basename(datapath))
    content_code = generate_content_code(datapath)
    data_code = generate_data_code(datapath)
    instance_code = generate_instance_code(datapath)

    iscc_code = ic.gen_iscc_code((meta_code["iscc"], content_code["iscc"], data_code["iscc"], instance_code["iscc"]))
    iscc_obj = ic.Code(iscc_code["iscc"])

    return {
        "meta": meta_code,
        "content": content_code,
        "data": data_code,
        "instance": instance_code,
        "iscc_obj": iscc_obj
    }

def generate_content_code(datapath):
    mimetype, _ = mimetypes.guess_type(datapath)
    
    if mimetype is None:
        print(f"Unbekannter Dateityp: {datapath}")
        sys.exit(1)
    
    if mimetype.startswith('text'): #or mimetype.find('wordprocess'): or mimetype.find('wordprocess'):
        text = idk.text_extract(datapath)
        return ic.gen_text_code_v0(text)
    elif mimetype.startswith('image'):
        image = Image.open(datapath)
        normalized_image = idk.image_normalize(image)
        return ic.gen_image_code_v0(normalized_image)
    elif mimetype.startswith('video'):
        video_features = idk.video_features_extract(datapath)
        return ic.gen_video_code_v0(video_features)
    elif mimetype.startswith('audio'):
        print("audio content code generierung.")
        audio_features = idk.audio_features_extract(datapath)
        return ic.gen_audio_code(audio_features["fingerprint"])
    else:
        print(f"Unbekannter Dateityp: {mimetype}")
        sys.exit(1)

def generate_data_code(datapath):
    with open(datapath, "rb") as stream:
        return ic.gen_data_code(stream)

def generate_instance_code(datapath):
    with open(datapath, "rb") as stream:
        return ic.gen_instance_code(stream)

def generate_semantic_code(datapath):
    mimetype, _ = mimetypes.guess_type(datapath)
    if mimetype and mimetype.startswith('text'):
        return sct.code_text_semantic(datapath)
    elif mimetype and mimetype.startswith('image'):
        return sci.code_image_semantic(datapath, bits=64)
    else:
        print(f"Unbekannter Dateityp: {mimetype}")
        sys.exit(1)

def compare_semantic_codes(code_a, code_b, bits):
    if code_a and code_b:
        code_a_str = code_a.value if hasattr(code_a, "value") else str(code_a)
        code_b_str = code_b.value if hasattr(code_b, "value") else str(code_b)
        if code_a_str and code_b_str:
            try:
                distance = sct.iscc_distance(code_a_str, code_b_str)
                return hamming_to_cosine(distance, bits)
            except binascii.Error:
                # Invalid ISCC code format
                return None
    return None

def compare_iscc_codes(original_codes, comparison_codes, mimetype=None):
    # Perform the similarity checks
    meta_sim = ic.iscc_similarity(original_codes["meta"]['iscc'], comparison_codes["meta"]['iscc'])
    meta_dis = ic.iscc_distance(original_codes["meta"]['iscc'], comparison_codes["meta"]['iscc'])

    content_sim = ic.iscc_similarity(original_codes["content"]['iscc'], comparison_codes["content"]['iscc'])
    content_dis = ic.iscc_distance(original_codes["content"]['iscc'], comparison_codes["content"]['iscc'])

    data_sim = ic.iscc_similarity(original_codes["data"]['iscc'], comparison_codes["data"]['iscc'])
    data_dis = ic.iscc_distance(original_codes["data"]['iscc'], comparison_codes["data"]['iscc'])

    instance_sim = ic.iscc_similarity(original_codes["instance"]['iscc'], comparison_codes["instance"]['iscc'])
    instance_dis = ic.iscc_distance(original_codes["instance"]['iscc'], comparison_codes["instance"]['iscc'])

    semantic_sim, semantic_dis = None, None
    if (mimetype and mimetype.startswith('text')) or (mimetype and mimetype.startswith('image')):
        semantic_sim = compare_semantic_codes(original_codes["semantic"]['iscc'], comparison_codes["semantic"]['iscc'], 64)
        semantic_dis = ic.iscc_distance(original_codes["semantic"]['iscc'], comparison_codes["semantic"]['iscc'])

    return {
        "meta_sim": meta_sim, "meta_dis": meta_dis,
        "content_sim": content_sim, "content_dis": content_dis,
        "data_sim": data_sim, "data_dis": data_dis,
        "instance_sim": instance_sim, "instance_dis": instance_dis,
        "semantic_sim": semantic_sim, "semantic_dis": semantic_dis
    }

def hamming_to_cosine(hamming_distance: int, dim: int) -> float:
    """Approximate the cosine similarity for a given hamming distance and dimension"""
    return 1 - (2 * hamming_distance) / dim

def print_output(comparison_codes, comparison_file, similarity_results, mimetype=None):
    print(f"Vergleichsobjekt: {os.path.basename(comparison_file)}")
    print(comparison_codes['iscc_obj'].uri)
    print(f"Meta:       {similarity_results['meta_sim']}%; Distance: {similarity_results['meta_dis']} Bits; Cosine Similarity: {hamming_to_cosine(similarity_results['meta_dis'], 64)*100}%")
    print(f"Content:    {similarity_results['content_sim']}%; Distance: {similarity_results['content_dis']} Bits; Cosine Similarity: {hamming_to_cosine(similarity_results['content_dis'], 64)*100}%")
    print(f"Data:       {similarity_results['data_sim']}%; Distance: {similarity_results['data_dis']} Bits; Cosine Similarity: {hamming_to_cosine(similarity_results['data_dis'], 64)*100}%")
    print(f"Instance:   {similarity_results['instance_sim']}%; Distance: {similarity_results['instance_dis']} Bits; Cosine Similarity: {hamming_to_cosine(similarity_results['instance_dis'], 64)*100}%")
    
    if (mimetype and mimetype.startswith('text')) or (mimetype and mimetype.startswith('image')):
        print(f"Semantic:   {similarity_results['semantic_sim']*100}%; Distance: {similarity_results['semantic_dis']} Bits")

    print("\n")

def update_markdown(original_data_path, original_codes, comparison_file, comparison_codes, similarity_results, mimetype=None):
    header = "|-----------------------------------------------------------------------------------------------|\n| Filename                      | Meta-Code     | Content-Code  | Data-Code     | Instace-Code  |"
    original = f"| {os.path.basename(original_data_path)} | {original_codes['iscc_obj'].uri} | {original_codes['meta']['iscc']} | {original_codes['content']['iscc']} | {original_codes['data']['iscc']} | {original_codes['instance']['iscc']} |"
    if (mimetype and mimetype.startswith('text')) or (mimetype and mimetype.startswith('image')):
        header = "|-------------------------------------------------------------------------------------------------------------------|\n| Filename                      | Meta-Code     | Semantic-Code     | Content-Code  | Data-Code     | Instace-Code  |"
        original = f"| {os.path.basename(original_data_path)} | {original_codes['meta']['iscc']} | {original_codes['semantic']['iscc']} | {original_codes['content']['iscc']} | {original_codes['data']['iscc']} | {original_codes['instance']['iscc']} |"
    
    dir = os.path.dirname(original_data_path)
    variation = os.path.basename(dir) ## directory of file
    datatype = mimetype.split("/")
    filetype = original_data_path.split(".")
    savePlace = f"../Testdaten/Ergebnisse/result_{datatype[0]}_{filetype[1]}_{variation}.md"

    if not os.path.exists(savePlace):
        with open(savePlace, "w") as file:
            file.write(header + "\n" + original + "\n")
            file.write("| ----------------------------- | ------------- |" + (" ----------------- |" if mimetype and mimetype.startswith('text') or mimetype and mimetype.startswith('image') else "") + " ------------- | ------------- | ------------- |\n")

    result_line = f"| {os.path.basename(comparison_file)} | {similarity_results['meta_sim']}% / {similarity_results['meta_dis']} Bits | {similarity_results['content_sim']}% / {similarity_results['content_dis']} Bits | {similarity_results['data_sim']}% / {similarity_results['data_dis']} Bits | {similarity_results['instance_sim']}% / {similarity_results['instance_dis']} Bits |"
    
    if (mimetype and mimetype.startswith('text')) or (mimetype and mimetype.startswith('image')):
        result_line = f"| {os.path.basename(comparison_file)} | {similarity_results['meta_sim']}% / {similarity_results['meta_dis']} Bits | {similarity_results['semantic_sim']*100}% / {similarity_results['semantic_dis']} Bits | {similarity_results['content_sim']}% / {similarity_results['content_dis']} Bits | {similarity_results['data_sim']}% / {similarity_results['data_dis']} Bits | {similarity_results['instance_sim']}% / {similarity_results['instance_dis']} Bits |"
    
    with open(savePlace, "a") as file:
        file.write(result_line + "\n")

def main(args):
    original_data_path, directory_data_path = check_args(args)
    
    # Generate ISCC codes for the original file
    original_codes = generate_iscc_codes(original_data_path)
    mimetype, _ = mimetypes.guess_type(original_data_path)

    # Generate semantic code if it's a text file
    if (mimetype and mimetype.startswith('text')) or (mimetype and mimetype.startswith('image')):
        original_codes["semantic"] = generate_semantic_code(original_data_path)

    # Process each file in the comparison directory
    comparison_files = [f for f in listdir(directory_data_path) if isfile(join(directory_data_path, f))]
    
    for comparison_file in comparison_files:
        comparison_path = join(directory_data_path, comparison_file)
        comparison_codes = generate_iscc_codes(comparison_path)
        
        # Generate semantic code if it's a text file
        if (mimetype and mimetype.startswith('text')) or (mimetype and mimetype.startswith('image')):
            comparison_codes["semantic"] = generate_semantic_code(comparison_path)
        
        # Compare ISCC codes and print output
        similarity_results = compare_iscc_codes(original_codes, comparison_codes, mimetype)
        print_output(comparison_codes, comparison_file, similarity_results, mimetype)
        update_markdown(original_data_path, original_codes, comparison_file, comparison_codes, similarity_results, mimetype)

if __name__ == "__main__":
    main(sys.argv)
