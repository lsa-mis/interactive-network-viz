import json, re
from bs4 import BeautifulSoup
import networkx as nx
import matplotlib.pyplot as plt
import math

def loadScalarData(input_file):
    # loads JSON data exported from the Scalar API Explorer tool
    # and parses as a dictionary for further manipulation with Python here

    data_for_output = {}

    with open(input_file, "r", encoding="utf-8") as read_file:
        data = json.load(read_file, strict=False)
        for key in data:
            out_dict = data[key]
            
            # also add the name of the current dictionary to the dcitionary itself and assign to the key 'key'
            # (because we're outputting a list of dictionaries, the key name would be lost otherwise)

            out_dict['key'] = key
            data_for_output[key] = out_dict
    
    return data_for_output

def getTagsAndTaggedNodes(reference_dict, excludeMedia=True):
    final_list_links = []
    nodes_identified_in_links = []


    for key in reference_dict:
        current_item = reference_dict[key]
        if 'urn:scalar:tag:' in current_item['key']:
            body = current_item['http://www.openannotation.org/ns/hasBody'][0]['value']
            target = current_item['http://www.openannotation.org/ns/hasTarget'][0]['value']

            # ignore tags here that involve media nodes (almost always images)
            if excludeMedia:
                if 'media' in body or 'media' in target:
                    continue
            
            if body not in nodes_identified_in_links:
                nodes_identified_in_links.append(body)

            if target not in nodes_identified_in_links:
                nodes_identified_in_links.append(target)
            
            tag_dict = {
                'source': body,
                'target': target,
            }
            
            final_list_links.append(tag_dict)
    
    return final_list_links, nodes_identified_in_links

def parseNodes(nodes_identified_in_links, lookForImages = True, lookForText= True):
    # note to self - add logic for lookFor parameters
    final_list_nodes = []
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
            # if reference to media found, fetch URL and description from media page
                print("\n")
                content = reference_dict[node]["http://rdfs.org/sioc/ns#content"][0]['value']
                # urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
                # print(urls[0])
                soup = BeautifulSoup(content, "html.parser")
                imageURL = soup.find("a")["href"]
                description = soup.text

                # ceate an abbreviated description (to encourage users to go to Scalar for full description)
                if len(description) > 80:
                    description = description[0:100] + "..."
        

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

    return final_list_nodes



def generateBetweennessCentrality(final_list_links, final_list_nodes):
    # use networkx to generate betweennenss centrality for nodes and return as dict


    nodes_for_nx = [node['id'] for node in final_list_nodes]
    edges_for_nx = [(n['source'],n['target']) for n in final_list_links]


    print(edges_for_nx)
    print(nodes_for_nx)
    G=nx.Graph()
    G.add_nodes_from(nodes_for_nx)
    G.add_edges_from(edges_for_nx)
    nx.draw(G)
    plt.show()

    return nx.betweenness_centrality(G)


def addBetweennessCentralityToNodes(betweenness_centrality_scores, final_list_links, final_list_nodes):
    final_output = {}
    final_output['links'] = final_list_links
    final_output['nodes'] = []

    for node in final_list_nodes:
        current_bc_score = betweenness_centrality_scores[node['id']]
        # let's convnert this to a 0 to 100 score, roundng up 
        node['betweenness_centrality_score'] = math.ceil(current_bc_score * 100)
        final_output['nodes'].append(node)
    # print(final_output['nodes'])

    return final_output


input_file = "scalar_output.json"
output_file = "cleaned_test.json"

reference_dict = loadScalarData(input_file)

final_list_links, nodes_identified_in_links = getTagsAndTaggedNodes(reference_dict)
final_list_nodes = parseNodes(nodes_identified_in_links)

betweenness_centrality_scores = generateBetweennessCentrality(final_list_links, final_list_nodes)

final_output = addBetweennessCentralityToNodes(betweenness_centrality_scores, final_list_links, final_list_nodes)



with open(output_file, "w") as write_file:
    json.dump(final_output, write_file)
    print('clean data successfully written to disk as "data_file.json"')

