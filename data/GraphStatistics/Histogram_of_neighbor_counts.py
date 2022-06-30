# This script will be used to generate the histogram of neighbor counts for certain categories of nodes.
# Files are saved where this file is located or where it is run from
import numpy
import os
import sys
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../code/")
except:
    pass
from RTXConfiguration import RTXConfiguration
RTXConfig = RTXConfiguration()
RTXConfig.live = "Production"
import sqlite3
import matplotlib.pyplot as plt


def get_sql_filepath():
    try:
        pathlist = os.path.realpath(__file__).split(os.path.sep)
    except NameError:
        pathlist = os.path.realpath(os.getcwd()).split(os.path.sep)
    RTXindex = pathlist.index("RTX")
    filepath = os.path.sep.join([*pathlist[:(RTXindex + 1)], 'code', 'ARAX', 'KnowledgeSources', 'KG2c'])
    sqlite_name = RTXConfig.kg2c_sqlite_path.split("/")[-1]
    sqlite_file_path = f"{filepath}{os.path.sep}{sqlite_name}"
    if os.path.exists(sqlite_file_path):
        pass
    else:
        os.system(
            f"scp {RTXConfig.kg2c_sqlite_username}@{RTXConfig.kg2c_sqlite_host}:{RTXConfig.kg2c_sqlite_path} {sqlite_file_path}")
    return sqlite_file_path

sqlite_file_path = get_sql_filepath()
connection = sqlite3.connect(sqlite_file_path)
cursor = connection.cursor()
# Extract the neighbor count data
category = 'biolink:Disease'
sql_query = f"select id from nodes where all_categories like '%{category}%';"
#cursor.execute(sql_query)
node_ids = [x[0] for x in cursor.execute(sql_query)]
node_keys_str = "','".join(node_ids)  # SQL wants ('node1', 'node2') format for string lists
sql_query = f"SELECT N.neighbor_counts " \
            f"FROM neighbors AS N " \
            f"WHERE N.id IN ('{node_keys_str}')"
cursor.execute(sql_query)
rows = cursor.fetchall()
rows = [curie_id.replace("\'","'").replace("''", "'") if "'" in curie_id else curie_id for curie_id in rows]
connection.close()

# Load the counts into a dictionary
neighbor_counts = [eval(x[0])['biolink:NamedThing'] for x in rows]
# export the data to a csv file
neighbor_counts_np = numpy.asarray(neighbor_counts)
try:
    numpy.savetxt(f"{os.path.dirname(os.path.abspath(__file__))}/{category}_neighbor_counts.csv", neighbor_counts_np, delimiter=",", fmt="%d")
except NameError:
    numpy.savetxt(f"{os.getcwd()}/{category}_neighbor_counts.csv", neighbor_counts_np, delimiter=",", fmt="%d")

# And then plot the histogram
plt.hist(neighbor_counts_np, bins=100)
plt.title(f"Histogram of neighbor counts for {category}")
plt.xlabel("Neighbor count")
plt.ylabel("Frequency")
try:
    plt.savefig(f"{os.path.dirname(os.path.abspath(__file__))}/{category}_neighbor_counts.png")
except NameError:
    plt.savefig(f"{os.getcwd()}/{category}_neighbor_counts.png")
plt.show()

# Also plot the percentiles
percentiles = numpy.percentile(neighbor_counts_np, numpy.linspace(0, 100, 100))
#percentiles = numpy.percentile(neighbor_counts_np, [0, 25, 50, 75, 100])
plt.plot(percentiles)
plt.title(f"Percentiles of neighbor counts for {category}")
plt.xlabel("Percentile")
plt.ylabel("Neighbor count")
try:
    plt.savefig(f"{os.path.dirname(os.path.abspath(__file__))}/{category}_neighbor_counts_percentiles.png")
except NameError:
    plt.savefig(f"{os.getcwd()}/{category}_neighbor_counts_percentiles.png")

# CONCLUSION: it appears that a simple multiplication of the normalized neighbor count by the result score will be fine
# when re-ranking the results by specificity