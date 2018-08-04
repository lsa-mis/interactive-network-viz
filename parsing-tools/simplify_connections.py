import json, re
from bs4 import BeautifulSoup


# Dicts and lists to store network information
# This will be used to assemble a network viz later
# With the specification of tags in a "links" sub-dictionary
# and node descriptions in a "nodes" sub-dictionary

data_for_viz = []
reference_dict = {}
final_list_links = []
final_list_nodes = []
nodes_identified_in_links = []


input_file = "scalar_output.json"
output_file = "cleaned_test.json"

with open(input_file, "r", encoding="utf-8") as read_file:
    data = json.load(read_file, strict=False)
    for key in data:
        out_dict = data[key]
        out_dict['key'] = key
        data_for_viz.append(out_dict)
        reference_dict[key] = out_dict

for item in data_for_viz:
    if 'urn:scalar:tag:' in item['key']:
        body = item['http://www.openannotation.org/ns/hasBody'][0]['value']
        target = item['http://www.openannotation.org/ns/hasTarget'][0]['value']

        # ignore tags here that involve media nodes (almost always images)

        if 'media' in body or 'media' in target:
            continue
        
        if body not in nodes_identified_in_links:
            nodes_identified_in_links.append(body)

        if target not in nodes_identified_in_links:
            nodes_identified_in_links.append(target)
        
        # print('Body = ' + body)
        # print('Target = ' + target + '\n')
        # print(body)
        # print(target)
    
        tag_dict = {
            'source': body,
            'target': target,
        }
        
        final_list_links.append(tag_dict)
# print(nodes_identified_in_links)

for node in nodes_identified_in_links:
    current_node_dict = reference_dict[node]
    url = node
    _id = node
    _name = ""
    photoURL = ""
    description = ""
    extraData = "no"

    # look for reference to media
    references = current_node_dict.get("http://purl.org/dc/terms/references")
    mediaReferenced = None
    imageURL = None
    description = None
    if references:
        if "media" in references[0]["value"]:
            mediaReferenced = references[0]["value"]
    if mediaReferenced:
        # if reference to media found, fetch URL and description from media page
        print("\n")
        content = reference_dict[node]["http://rdfs.org/sioc/ns#content"][0]['value']
        # urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        # print(urls[0])
        soup = BeautifulSoup(content, "html.parser")
        imageURL = soup.find("a")["href"]
        description = soup.text       
    

    # get rid of part of URL after period (multiple versions in Scalar)
    if url[-2] == '.':
        url = url[0:-2]
    elif url[-3] == '.':
        url = url[0:-3]
    elif url[-4] == '.':
        url = url[0:-4]

    
    try:
        # make sure the node is fetching the name correctly, assign to _name
        _name = current_node_dict['http://purl.org/dc/terms/title'][0]['value']
        # print(title)

    except:
        _name = node

    node_out = {
        'id' : _id,
        'name' : _name,
        'url' : url,
        'colour':	"#2a2a2a"
    }

    if imageURL:
        node_out["imageURL"] = imageURL
        extraData = "yes"
    if description:
        node_out["description"] = description
        extraData = "yes"
    node_out["extraData"] = extraData


    final_list_nodes.append(node_out)

final_output = {}
final_output['links'] = final_list_links
final_output['nodes'] = final_list_nodes

# print(final_output['nodes'])


with open(output_file, "w") as write_file:
    json.dump(final_output, write_file)
    print('clean data successfully written to disk as "data_file.json"')