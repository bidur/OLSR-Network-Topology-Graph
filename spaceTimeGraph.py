# /usr/bin/python

import socket, sys, time, datetime , os, copy

olsrIP = '127.0.0.1'
txtInfoPort = 2006
dataInterval = 5 #10 second interval ( assuming the topology does not changes for at least 10 seconds)
dict_nodes = dict() # holds the node and their label for the ALL subgraph
dict_links = dict() # holds the node and their links for the ALL subgraph
dict_of_nodes_temp = dict() # holds the node and their label for the current subgraph
dict_of_old_nodes_temp = dict() # holds the node and their label for the previous subgraph

#list_temporalLink = list() # list to hold the set of temporal links from current subgraph i to previous subgraph i-1



def GetOLSRtxtInfo():
  try:
    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    s.connect( (olsrIP,txtInfoPort) ) 
    s.send( "/topology")  # /all, /neigh,  /link, /route, /topology
    txtInfo = s.recv( 16777216 ) 
    s.close()
  except socket.error, msg:
    print "GetOLSRtxtInfo() : socket error. Please check the status of OLSRD " + str( msg )
    return None

  return txtInfo


def getNodeName(nodeIP,graphCtr,nodeCtr):

 # check if this nodeIP is already assigned a name
  if nodeIP in dict_of_nodes_temp.values():    
    nodeName = [key for key, value in dict_of_nodes_temp.iteritems() if value == nodeIP][0]
    return (nodeName,nodeCtr)
  
  else:# if this nodeIP is not assined a name then give it a name and Update it to dict_of_nodes_temp

    nodeName = 'n_'+str(graphCtr)+'_'+str(nodeCtr)    
    dict_of_nodes_temp[nodeName]= nodeIP
    
    nodeCtr+=1
    return (nodeName,nodeCtr)


    
def printSubGraph(dict_nodes,subgraphID):

    opStr='subgraph cluster'+str(subgraphID)+"{\n\nlabel="+'"t='+str(subgraphID*dataInterval)+'"'+ " \n"
    opLink=''
    opLabel=''

    #now define the label to be shown for each node
    for key in dict_nodes.keys():
	#check if the node is for this subgraph

        if key.count('n_'+str(subgraphID)+'_'):
          
          opLabel+= "\n"+ key + '[label="'+dict_nodes[key]+'"];'

          if key in dict_links.keys(): # if a link from this node is defined Eg. will be like this dict_links{'n_0_0':'n_0_1' , 'n_0_1':'n_0_2,n_0_3'}
            listValues = (dict_links[key]).split(',')
            for i in range(0,len(listValues)):
              opLink+= "\n "+ key +" -- " + listValues[i] + ";"
              
              
        

    #defining label and link finish, now combind them into opStr
    opStr+= opLabel +"\n"+  opLink +"\n};"

    return opStr
    

def generateSpaceTimeGraph(graphCtr):
  outputStr="graph {\nrankdir=LR;\nlabeljust="+'"l";'
  #get all subgraphs
  for i in range (0,graphCtr):
    outputStr += "\n \n" + printSubGraph(dict_nodes,i)
 
  
  outputStr += "\n \n}"

  # create a .dot file with the graph information
  fo = open("spaceTimeGraph.dot","w")
  fo.write(outputStr)
  fo.close()

  #open the file with dot program
  os.system("dot -o spaceTimeGraph.ps -T ps spaceTimeGraph.dot")
  



def main(): 
  print "Reading txtinfo at an interval of "+str(dataInterval)+" seconds"
  graphCtr = 0
  nodeCtr = 0

  while True:    
    txtInfo = GetOLSRtxtInfo()
    
    if txtInfo is not None:
      
      #print "\n", datetime.datetime.now(), "\n", txtInfo
      lstInfo = txtInfo.split("\n")
      #print lstInfo[5]

      
      for i in range (5,len(lstInfo)):
        #if empty string got then ignore that line
        if (lstInfo[i]==''):
          continue
        
        lstNodes =  lstInfo[i].split("\t")

        node1 = lstNodes[0].replace(" ","") #node1 and node2 have the ipaddress eg 192.168.8.8        

        node2 = lstNodes[1].replace(" ","")
              
        nodeName1,nodeCtr = getNodeName(node1,graphCtr,nodeCtr)
        nodeName2,nodeCtr = getNodeName(node2,graphCtr,nodeCtr)

        #check if nodeName1 is already inserted as key. If yes then append nodeName2 separated by comma
        if(dict_links.get(nodeName1)):
          dict_links[nodeName1]= dict_links[nodeName1] +','+nodeName2
        else:
          dict_links[nodeName1] = nodeName2 # add the link information


    time.sleep( dataInterval )
    dict_nodes.update(dict_of_nodes_temp)# add nodes info to the global dictionary which have all nodes
    #print 'dict_of_nodes_temp'
    #print dict_of_nodes_temp
    #dict_of_old_nodes_temp = copy.deepcopy(dict_of_nodes_temp)
    dict_of_old_nodes_temp.clear()
    dict_of_old_nodes_temp.update(dict_of_nodes_temp)
    #print dict_of_old_nodes_temp
    dict_of_nodes_temp.clear() # clear the nodes for last subgraph
 

    #now print the graph
    generateSpaceTimeGraph(graphCtr)
    print "\n" +str(graphCtr)+' subgraph printed '
    graphCtr += 1  # next subgraph
    nodeCtr = 0 # initialize the node counter for next subgraph
  

if __name__ == "__main__":
  main()
