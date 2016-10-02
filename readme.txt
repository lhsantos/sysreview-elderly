The files are organized in the following way:
  <database name>.bib has all the references for the base search (without the "cognitive" keyword restriction)
  <database name>-cog.bib has all the references for the search that also (AND) contain the "cognitive" keyword

PUBMED:
  PubMed results can only be directly exported to XML format, so the XSLT file 'pubmed2bibtex.xsl' was used
  to transform that data into BibTex. This file was created based on the file available at
  'http://svn.gna.org/viewcvs/kbibtex/trunk/xslt/' with modifications:
  - remove '[' and ']' from title, when it exists
  - updated to handle dates in <MedlineDate> format as well
  - page number ranges are converted from NN-NN to NN--NN
  
  The XML is download from the database webpage and the DOCTYPE tag is replaced for:
  <!DOCTYPE PubmedArticleSet SYSTEM "nlmmedlinecitationset_160101.dtd">
  The DTD file was downloaded from 'https://www.nlm.nih.gov/databases/dtd/' on Oct/2016
  The final XML file is processed into a bib file using xsltproc command line tool.
