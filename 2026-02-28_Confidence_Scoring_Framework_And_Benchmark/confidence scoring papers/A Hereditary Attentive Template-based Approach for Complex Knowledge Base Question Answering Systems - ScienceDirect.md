## Expert Systems with Applications

```
Volume 205, 1 November 2022, 117725
```

# A Hereditary Attentive Template-based Approach for Complex

# Knowledge Base Question Answering Systems

Jorão Gomes Jr. , Rômulo Chrispim de Mello , Victor Ströele , Jairo Francisco de Souza



## Highlights

- Knowledge base question answering systems struggle to deal with  complex questions.
- A template matching approach for complex question answering
- A Hereditary Attention that inherits the information in a bottom-up  way.
- Limitations of datasets for C-KBQA and a new cleaned version of a C- KBQA dataset.

## Abstract

Knowledge Base Question Answering systems (KBQA) aim to find answers to natural language questions over a knowledge base. This  work presents a template matching approach for Complex KBQA systems (C-KBQA) using the combination of Semantic Parsing and  Neural Networks techniques to classify natural language questions into answer templates. An attention mechanism was created to  assist a Tree-LSTM in selecting the most important information. The approach was evaluated on the LC-Quad 1, LC-Quad 2,  ComplexWebQuestion, and WebQuestionsSP datasets, and the results show that our approach outperforms other approaches on three  datasets.

## Keywords

Question Answering; Complex Question; Knowledge Base; Semantic Parsing; Neural Networks

## 1. Introduction

Question Answering (QA) systems have the purpose of retrieving the most relevant information (answer) to a search question made  
by a user (Croft, Metzler, & Strohman, 2010). Knowledge base (KB) is a data model based on a semantic network, which uses a triple

format (subject, predicate, object) to represent and relate the information contained within a data domain (Ji et al., 2020, Popping,  
2003 ). QA systems that made use of KB are called Knowledge Base Question Answering (KBQA). The KBQA systems use those semantic  
structures, for example, Freebase (Bollacker, Cook, & Tufts, 2007), Wikipedia (Lehmann et al., 2015) or Wikidata (Vrandečić & Krötzsch,  
2014 ) to answer a question.

KBQA systems need to deal with different kinds of questions. We can divide them into two groups: simple and complex questions.  
Simple questions are those that contain direct answers and only direct entities that need to be detected to answer a question (Bordes,  
Usunier, Chopra, & Weston, 2015). Complex questions need more information than the explicit features that can be extracted from  
simple questions. Therefore, it is necessary to use advanced query operations to collect the answer from the KB, such as exploiting  
indirect relations among entities, multi-relations, qualitative and quantitative constraints, and others (Bao et al., 2016, Qiu, Wang et al.,  
2020 ). However, it is hard to extract and map the features of a complex question into a KB since the questions have indirect relations,  
qualitative information, and many entities/predicates. Currently, KBQA systems achieve better results when answering simple  
questions, and Complex Knowledge Base Question Answering (C-KBQA) systems turned the goal to the recent researches in the QA  
field (Hua et al., 2020a, Hua et al., 2020b, Qiu, Zhang et al., 2020).

The extraction of the features of a question and the mapping into a KB is called semantic parsing. Semantic parsing is the mapping of  
Natural Language Question (NLQ) to a meaning representation that can be further represented as a logic form (Tong, Zhang, & Yao,  
2019 ). In this process, the NLQ is transformed into an intermediate format that can represent the structure of the question (Trivedi et  
al., 2017, Wu et al., 2019). Similar to the divide and conquer problem, breaking an NLQ into a list of intermediate representations is  
possible. However, the use of semantic parsing alone on a complex question can be computationally expensive due to the number of  
operations that must be performed to find the structure that answers a question (Höffner et al., 2017).

Template matching can perform the semantic parsing process for C-KBQA. First, a set of pre-defined answer templates are defined,  
and slots to be filled (e.g., subject, predicate, and constraints) are created. These answer templates are related to the KB and have  
different formats to deal with multi-hops and constraints. Then, the slots are filled with features of the complex question to answer  
the question. The combination of Semantic Parsing and Neural Networks came as the next step to solve the C-KBQA problem (Ding et  
al., 2019, Luo et al., 2018). A Neural Network can classify the templates given the feature extracted from a complex question to perform

the template matching. This approach consists of training a neural network to match a set of semantic parsing rules; in this paper, it is  
a set of answer templates. This can reduce the computationally cost of using Semantic parsing alone.

This work addresses the problem of answering complex questions with a semantic template-matching approach for C-KBQA systems.  
The C-KBQA approach uses the combination of Semantic Parsing and Neural Networks techniques to determine the answer templates  
that a complex question fits. Moreover, an attention mechanism was created to assist the neural network in selecting the most  
important information. In the so-called Hereditary Attention, each neural network cell inherits the attention from another neural  
network cell in a bottom-up way. However, good datasets for C-KBQA are an open challenge, and it is a limitation to perform and  
evaluate a template matching approach for C-KBQA. We released a new version of a C-KBQA dataset containing answer templates to  
mitigate this problem.

The main contributions of this work are threefold: (i) a new C-KBQA approach for template matching; (ii) a hereditary attention  
mechanism to assist in question semantic extraction that achieved promising results and better accuracy than related work; (iii) a  
new preprocessed version of a dataset for complex question answering that other researchers can use.

The remainder of the paper is structured as follows: in Section 2 the background and related work are presented. In Section 3 the  
details of each step our C-KBQA approach are presented. In Section 4 the evaluation setup and dataset pre-processing methodology are  
described. Section 5 our results and challenges are presented. Finally, in Section 6 presents our conclusions remarks and future  
directions are presented.

## 2. Related work

C-KBQA problem can be addressed in different ways. For C-KBQA systems, the complex questions can be divide into two subgroups:  multi-hop questions and constraint questions. To handle multi-hop questions, a C-KBQA system needs to handle entities and relations  extracted from the natural question (Li, Hu, & Zou, 2020). The entities detected in those questions need to be linked, and it is necessary to deal with indirect relations, unlike simple questions, which can be answered directly. The KB triple connections (subject object) are recovered, and systems make hops between the objects detected in the NLQ and the KB relations to get the target entity. In constraint questions, the NLQ often includes some restrictions that limit the answering options for a given question (Shin & Lee, 2020).

Those restrictions can be of several types, such as temporal, ordinal, quantitative, and others. The constraints can modify the main  subjects of an NLQ and consequently change the answer. An NLQ can also represent both a multi-hop and constraint question.In Yin, Ge, and Wang (2014) the authors dealt with the multi-hops questions with a Semantic Parsing approach. The author tries to  directly map a complex question, creating a set of rules to define the type of complex question and match them into a logical  format. Jia, Abujabal, Saha Roy, Strötgen, and Weikum (2018) present advances to solve constraint questions with a module capable to  deal with constraint questions. This work creates a new module, called TEQUILA, that addresses part of the problem related to  complex temporal questions, re-using and improving other KBQA systems like AQQU (Bast & Haussmann, 2015), and QUINT (Abujabal,  Yahya, Riedewald, & Weikum, 2017). Both AQQU and QUINT creates template question to answer simple questions, however, the  systems have limited coverage for complex questions. TEQUILA came as a side module to improve the answer to temporal questions  using decomposition and re-composition rules. We address the problem of answering complex questions with a template matching  
approach as AQQU and QUINT, however, our approach is capable to deal with a complex question based on the semantic structure of  an NLQ.

Talmor and Berant (2018) propose a system that decomposes complex questions into a sequence of simple questions. The final answer  
is computed from the sequence of simple question answers, using a set o semantic parsing rules. The authors also present that  datasets for C-KBQA are a limitation and released a novel dataset for complex questions. Bhutani, Zheng, and Jagadish (2019) also  ddresses the complex question with decomposition technique in a system called TextRay, that searches for sub-graphs through a  combination of Semantic Parsing and Neural Networks. Two LSTM are used in the semantic matching model to extract the semantic  relation between the NLQ and the KB entities and relations. A new version of TextRay is present in Bhutani, Zheng, Qian, Li, and  Jagadish (2020) where the system handles the search of answers in multiple KB with an additional module that computes the  similarity among multiples KB. Similarly, a Neural Program Induction-based approach is presented by Ansari et al. (2019) to  decompose an NLQ and produce a program, i.e. a set of data manipulation operations that answers the NLQ. The authors state that  their model is noise-resilient and distant-supervised by the final answer alone. The combination of Semantic parsing and Neural  network is also used in this paper. We created a Hereditary Tree-LSTM that is capable to classify the template that an NLQ matches  given the semantic feature extracted from a complex question. Also, we present the problems with C-KBQA datasets and released a  new cleaned dataset to help in the C-KBQA dataset limitation. Although neural symbolic computing (Lamb et al., 2020) and other question decomposition approaches present promising results for C-KBQA and some of these approaches are less dependent on gold standards, template-based approaches are less time-consuming to train and generate more reasonable questions in most cases (Liu,  
Wei, Chang, & Sui, 2017).

Zafar, Napolitano, and Lehmann (2018) present a semantic parsing module for query generator. The so-called SQG detects subgraphs  paths in KB using Named Entity Disambiguation and Relation Extraction tasks. However, the SQG has a limited cover of complex  question types. In Lan, Wang, and Jiang (2019) a semantic parsing approach handles multi-hop questions but only type constraints,  e.g. the question “what state is Harvard College located?” contains an implicit answer type constraint of the form. The  authors applied a matching-aggregation model to measure the similarity between a question and a candidate answer. It allows them  to exploit word level interactions through bi-directional attention mechanisms. In Abdelkawi, Zafar, Maleshkova, and Lehmann (2019)  the authors reused the SQG and created two extra modules to better handle ordinal questions (constraint questions). Dileep et al.  (2021) presents a C-KBQA system over LC-QuAD 2.0. The authors presented that the XGBoost achieve good results in template  matching. Athreya, Bansal, Ngomo, and Usbeck (2021) also uses the Tree-LSTM for question answering on LC-QuAD 1.0 and shows that  Tree-LSTM can have good performance in questing answering. ReTrack (Chen et al., 2021) is neural semantic parsing framework for  KBQA that handles multi-hop questions but is not designed to handle constraint questions. The framework was designed to enhance  the controllability of transduction-based methods in both syntax and semantic level, and employs a modular architecture to allow  integration with new components. Finally, Diomedi and Hogan (2021) adopt a neural machine translation approach to translate an  NLQ into a structured query language (templates) and also present some limitations of C-KBQA datasets. Our approach differs from  other by applying a so-called Hereditary Attention to assist our Tree-LSTM architecture in dealing with complex questions. The  attention mechanism is used to emphasize the relevant parts of the question and so detect the target template. So, it is possible to  relate the constraint in the NLQ with the respective templates instead of subgraphs paths.

Given this overview of works in C-KBQA, we highlight the following points, which make our proposed approach distinct from the  previous ones:

1. A novel architecture for question answering using template matching. It is the so-called Hereditary Tree-LSTM. The architecture uses a Hereditary Attention, where each neural network cell inherits the semantic attention from another neural network cell, in a bottom-up way.

2. Datasets for C-KBQA are an open challenge and it is a limitation to perform and evaluate approaches for C-KBQA. Here, we present some limitations of one of the largest datasets for C-KBQA, the LC-QuAD 2.0 (Dubey, Banerjee, Abdelkawi, & Lehmann, 2019). These issues can cause systems to answer questions wrongly or mask errors when evaluating question answering systems. To mitigate this problem, a new version called LC-QuAD 2.1 containing answer templates was released. LC-QuAD 2.1 is a cleaned version of the original dataset, whiteout duplicated questions, malformed questions, and other problems present in the Section 4.

## 3. C-KBQA approach

In this section it is presented the C-KBQA approach used in this work.

## 3.1. Pre-processing

A template-based C-KBQA system can be divided into three steps: question parsing, question representation, and candidate ranking. Fig. 1 presents an overview of the three steps for the question “When was the director of Titanic born?”. In a nutshell, in the question representation step (step 1), semantic mapping is performed. The question representation step (step 2) structures the semantic mapping in a KB intermediate semantic format representation. Finally, the candidate ranking step (step 3) removes incorrect answers based on the type, entities, predicates, and semantics detected on the original question. In this paper, our goal is to present a novel solution for the question representation step (step 2).

We create a Neural Networks-based Semantic Parsing system to deal with complex questions using a combination of Semantic Parsing  and Neural Network techniques (question representation—step 2). Semantic parsing is the mapping of NLQ to a meaning representation that can be further represented as a logic form (Tong et al., 2019). In this process, the NLQ is transformed into an intermediate representation (Trivedi et al., 2017). We use a template matching approach where a question can be mapped into an intermediate representation (our template) of a KB.

![[Pasted image 20260301132551.png]]

Fig. 1. Template-based C-KBQA pipeline.

## 3.2. Classifier

A Recurrent Neural Network (RNN) is used to select the best-appropriated template based on the semantic of the question. Our  
template-based C-KBQA was created using a Tree-LSTM architecture. Usually, the Tree-LSTM is used for sentiment classification and  
semantic relatedness of sentence (Tai, Socher, & Manning, 2015). However, in this paper, we implemented a Tree-LSTM to create a C-  
KBQA system that will be able to extract the semantic of a question and decide the answer template that a question belongs to.

We implemented an attention mechanism to assist in selecting the most important information. Attention is used to emphasize the  
more relevant parts of a question and to preserve the context of the sentences (Bhutani et al., 2019, Bhutani et al., 2020, Vaswani et al.,  
2017 ). In the so-called Hereditary Attention mechanism, the attention layer inherits the children’s attention of each sub-tree of the

Tree-LSTM, passing this information on a bottom-up way. The combination of Tree-LSTM and hereditary attention is called Hereditary  
Tree-LSTM.

There are two types of Tree-LSTM: Child-Sum and N-Array. In the Child-Sum, the Tree-LSTM can have many children as the tree  
structure that was selected to be used, and in the N-Array the Tree-LSTM can have only N children per level (e.g., a binary tree). We  
used the Child-Sum Tree-LSTM version since we want to capture all the semantics behind a complex question composition.

The Tree-LSTM uses an input gate, forget gate, output gate, memory cell, and hidden state similar to the standard LSTM. As present  
in Tai et al. (2015), given a tree, let C(j) denote the set of children of node j, denotes the input, denotes the input gate, denotes  
the forget gate, denotes the output gate, denotes the memory cell, and denotes the hidden state. The Child-Sum Tree-LSTM  
transition equations are the following:
![[Pasted image 20260301132648.png]]
Ahmed, Samee, and Mercer (2019) and Miyazaki and Komachi (2018) presented that the attention mechanism for Tree-LSTM can   achieve good results for the semantic relatedness and sentiment classification of texts tasks. In this paper, a hereditary attention mechanism was created to assist the Tree-LSTM in focus only on the relevant information of a complex natural language question. The attention is applied successively in the set of children of each sub-tree and decides the features more relevant that have to be  emphasized to build the new hidden state of this sub-tree. In this way, the children’s hidden states of each sub-tree are weighted with  a “factor of importance”, until the root node be achieved (bottom-up). Fig. 2 presents an example of our hierarchical attention version  of the Tree-LSTM. The solid arrow presents the input of the attention layer and the dotted arrow presents the output after the  
weighted process.

The hereditary attention is based on the self dot product attention (Vaswani et al., 2017) with a scale factor. Three components are  used when creating attention mechanisms: query, key, and value. The query is the information that you are looking for. The key is the  set of assets that can be used when making a query. The value is the matched result for your query given the set of keys used. These  three components are used here as weight matrices, that will be learned during the training step. Each matrix is constructed using a  
linear layer. The attention created in this paper is similar to the presented in Zhang, Goodfellow, Metaxas, and Odena (2019), where  
the authors used the self dot attention for image generation tasks. However, the authors used convolution layers instead of the linear  
layers and do not have a normalization factor to weigh the information that will be preserved of each set o children.

![[Pasted image 20260301132817.png]]
Fig. 2. Hereditary Tree-LSTM.

Let denote all children’s hidden states of a given sub-tree concatenated (![[Pasted image 20260301133339.png|189]] ), d denote memory dimension of  
the Tree-LSTM. ![[Pasted image 20260301133439.png|133]]denote, respectively, the query, key, and value weight matrices, and ![[Pasted image 20260301133509.png|114]]denote,  
respectively, the query, key, and value bias. The query, key, and value matrix are constructed using the following equations:
![[Pasted image 20260301133256.png|676]]
The query, key, and value matrices are of dimension , where represents the number of children concatenated in (Eqs. (8), (9),  and (10)). The relation between the information that we are searching for (query matrix) and the set of components that can be used  when searching (key matrix) is now calculated. This relation is called energy matrix and it is calculated performing a matrix  multiplication ( ) between the query and key matrix.
![[Pasted image 20260301133638.png|682]]
The new energy matrix (Eq. (12)) is a matrix x that represents the energy that the hidden states have to this set of children (H).  Also, a re-scale factor is used as a normalization factor (Eq. (11)). In this step, our approach defers from Ahmed et al. (2019) as we do  not want to diminish the information of one child concerning the other child, but extract the most important information from both  children. So, the energy matrix is of size × instead of , as suggest for Ahmed et al. (2019).
To calculate the attention matrix, a softmax function is applied (Eq. (13)). The energy matrix is re-scale into the [0,1] scale. This matrix  
represents how much the information has to be re-weighted, highlighting the important information on this set of children. The  
attentive hidden states ( ) are calculated using a matrix multiplication between the value matrix and the attention weights  
(Eq. (14)).
![[Pasted image 20260301133712.png|695]]
The is of size and represents the pieces of information more important of the hidden states of those children set. Therefore,  as represented in Eq. (1), the new will be the sum of all children with attention (Eq. (15)).
![[Pasted image 20260301133744.png|687]]

The remaining equations are the same presented for the Tree-LSTM (Eqs. (2), (3), (4), (5), (6), and (7)), however, now all the operations  are taking into account the highlighted information of each sub-tree. The higher nodes on the Tree-LSTM are inheriting thehighlighted information from their children.

## 4. Implementation and evaluation

This section presents the training setup (e.g., dataset, data preprocessing, target, hyperparameter tuning, etc.) and evaluation  
methodology.
![[Pasted image 20260301134037.png|254]]
Fig. 3. Question length before sentence length normalization.

## 4.1. Dataset adaptation

The C-KBQA approach was evaluated using four datasets: LC-QuAD 1.0 (Lóscio et al., 2017), LC-QuAD 2.0 (Dubey et al., 2019),  ComplexWebQuestion (Talmor & Berant, 2018), and WebQuestionsSP (Yih, Richardson, Meek, Chang, & Suh, 2016). We perform some  changes on LC-Quad 2.0, ComplexWebQuestions, and WebQuestionsSP to suit template-based approaches. For example, LC-Quad 1.0 provides natural language questions and their corresponding template. Other datasets, however, provide the final SPARQL queries only. Therefore, dummy SPARQL templates were created, i.e. SPARQL queries with no entities.

The data processed for this study are helpful for other C-KBQA approaches. Besides template matching, these datasets can be used for  semantic parsing approaches, such as subgraph path detection or the creation of logical grammar rules. The processed datasets are  available for further research (Gomes Jr., de Mello, Ströele, & de Souza, 2021).

## 4.1.1. LC-QuAD 2.

The “Large Dataset for Complex Question Answering over Wikidata and DBpedia” version 2.0 (LC-QuAD-2) was the main experimental  dataset. The LC-QuAD-2 (Dubey et al., 2019) is one of the most recent datasets for C-KBQA. LC-QuAD-2 included more types of  complex questions, e.g., up to 6 hops questions and more constraint questions than the previous version. The dataset contains over  30,000 questions, composed of 21,258 entities and 1310 predicates, created using Amazon Mechanical Turk, a crowdsourcing
platform. The dataset presents the logical form of each question in SPARQL format. Wikidata (Vrandečić & Krötzsch, 2014) and DBpedia  2018 (Lehmann et al., 2015) were used as Knowledge Base. Also, the dataset contains a paraphrase question for almost all original  questions on the dataset.

When performing a crowdsourcing approach, inconsistencies can be inputted on the data (e.g., text duplication, missing information,  etc.). So, the dataset was preprocessed to deal with those types of problems. Other works, such as Diomedi and Hogan (2021), also  presented problems with the inconsistencies in the dataset. To standardize the dataset, all the instances with empty or duplicated  question fields were excluded to avoid any bias in the data during the separation of training, development, and testing sets. The  instances with two or more questions in the same id, e.g. “What was the name of Kartikeya child? Shiva?”, were also removed as we  could not ensure which question the answer was related to. The answer can be a KB entity or a boolean value in this example. Finally,  we notice that the original training and testing sets, provided by the authors of the dataset, had some questions that appeared in both  sets, and they were removed.

The above process was performed to create a more consistent dataset. The inconsistencies can make a QA system learn to answer  questions that real users do not make (e.g., questions so big or so small) or be overfitted on questions of the same type due to question  duplication. It was verified that some instances have a size incompatible with the rest of the dataset. The boxplot in Fig. 3 presents the length of all questions in the dataset before the normalization. Some questions have more than 500 characters and others less than 5  characters. We removed all the questions with more than 120 characters and less than 15 characters to make the data homogeneous.  Fig. 4 presents the results after the outliers removal (considering the question length).

The dataset contains a SPARQL-based logical form for each question. The original SPARQL was transformed into templates. These  templates are used as answer templates that are matched in the question representation step. The subject, predicates, objects, and  filters found in the original SPARQL were masked into dummy tokens (DUMMY_S, DUMMY_P, DUMMY_O, DUMMY_F). The templates  are so-called Dummy SPARQL templates, and in Fig. 5 it is presented the creation process of these templates. After this process, 29  unique Dummy SPARQL templates were created for the Wikidata KB, and 25 unique Dummy SPARQL templates were created in the 
DBpedia KB.

![[Pasted image 20260301134330.png]]
Fig. 4. Question length after sentence length normalization.

Several Dummy SPARQL templates have a similar semantic and only minor difference between the answer templates. The difference  
between two Dummy SPARQL templates can be only a projection on the subject or the object, or a restriction less than or greater than

a value (filter), for example. We performed a semantic analysis on the dummy SPARQL templates and grouped them by proximity  
between them. Seven items were analyzed to create each SPARQL group: the number of projections, hops, and filters and if the  
template contains a limit, order, count, or distinct logical operators. We order these items by the number of occurrences on the  
dummy SPARQL templates, and 12 unique dummy SPARQL groups for Wikidata and 10 unique dummy SPARQL groups for DBpedia  
were created. Fig. 6 presents the creation process of a dummy SPARQL group where the first template has a subject projection and the  
second has an object projection.

![[Pasted image 20260301134422.png]]
Fig. 5. Creation of dummy SPARQL templates.


![[Pasted image 20260301134433.png]]
Fig. 6. Creation of group dummy SPARQL templates by SPARQL approximation.

Table 1 presents the distribution of question for each Dummy SPARQL template ID and group ID for the Wikidata KB. Read GID as  
group ID, TID as template ID, #Q as the number of questions in the template ID, and #TQ as the number of questions in the group

when reading the names of the columns. The Tables show a high number of imbalanced data on the dataset, with different types of  
answer templates. The answer templates are of several types of complex questions, e.g., less/greater than or year restrictions, and  
multi-hops. Additional information for DBpedia 2018 can be found in Appendix. This cleaned version of the dataset is so-called LC-  
QuAD 2.1 in this paper.

[,belowfloat=15pt]

Table 1. Questions distribution by dummy template and dummy group ids for the Wikidata.
![[Pasted image 20260301134922.png|434]]
![[Pasted image 20260301135007.png|541]]
![[Pasted image 20260301135125.png|547]]
![[Pasted image 20260301135157.png|548]]
![[Pasted image 20260301135247.png|565]]
## 4.1.2. WebQuestionsSP And ComplexWebQuestions

WebQuestions Semantic Parsing (WebQuestionsSP) is a dataset based on WebQuestions (Berant, Chou, Frostig, & Liang, 2013).  However, the first version of WebQuestions does not have any logic form to be matched, and the WebQuestionsSP was released to fill  this gap (Yih et al., 2016). WebQuestionsSP contains questions in SPARQL format and fewer available questions than the original  WebQuestions because some questions were removed to avoid ambiguity.

ComplexWebQuestions (Talmor & Berant, 2018) is a dataset based on the WebQuestionsSP dataset. The authors modified the logic  form of WebQuestionsSP questions and added more constraint types to the original questions. These new types are composed of time, conjunctions, superlatives, and comparative constraints. Both WebQuestionsSp and ComplexWebQuestions use SPARQL as the logic form and Freebase as Knowledge Base.![[Pasted image 20260301135247.png]]

New templates for WebQuestionsSP and ComplexWebQuestions were created using the process described in the previous section. We  found 42 unique templates for WebQuestionsSP and 75 unique templates for ComplexWebQuestions. Both datasets present a huge  imbalanced distribution of questions per template type. This imbalanced scenario can leverage problems during the model training.  Therefore, we selected the most frequent in each dataset. Templates with less than 100 questions were removed from the  ComplexWebQuestions, and templates with less than 10 questions were removed from WebQuestionsSP. We used distinct thresholds  because WebQuestionsSP is significantly smaller than ComplexWebQiestions. In the end, 13 templates from WebQuestionsSP and 16  templates from ComplexWebQuestion were selected.

## 4.2. Setup

To evaluate the C-KBQA approach, the POS-tagger and Semantic Dependency Tree (DT) from the Stanford CoreNLP toolkit (Manning et  
al., 2014) were used to extract the semantic of a question and to create the tree structure used for the Tree-LSTM. The inputs for the  
Tree-LSTM were created using the FastText pre-trained word embedding (Bojanowski, Grave, Joulin, & Mikolov, 2017). Each word in  
the question was transformed into a word vector. Word embeddings reduce the computational complexity since the matrix  
operations through these word vectors are fast to compute. Also, the DT relations and POS-Tagger tokens were transformed into one-  
hot-encoding vectors. The word vector, the DT one-hot-encoding vector, and the POS-Tagger one-hot-encoding vector were  
concatenated to create the input vector. To decide which template a question matches, a softmax classifier is applied at the root node  
of the Tree-LSTM, and the cost function used is the negative log-likelihood.

```
Question type TID Precision Recall F1 Support
```

LC-QuAD, ComplexWebQuestions and WebQuestionSP datasets provide training and testing sets, and they were converted to  
templates according to the process described in Sections 4.1.1 LC-QuAD 2.0, 4.1.2 WebQuestionsSP And ComplexWebQuestions. The  
final training, validation and test subsets are available on Zenodo (Gomes Jr. et al., 2021). To evaluate the approach on LC-Quad 2.1, we  
have defined two training setups: a dataset without the paraphrase questions provided by the dataset and a dataset with these  
paraphrases. The paraphrase questions are used to evaluate the brittleness of the C-KBQA system when a question only with a few  
modifications is inserted and added to the training set. Both setups were performed in a stratified fashion, based on the dummy  
templates, due to the imbalanced scenario.

## 4.3. Classifier

A hyperparameter tuning step was performed to select the best model. Table 2 presents the values of the best model selected in the  
development set.

## 5. Result analysis

Four works were selected as baselines to compare with our C-KBQA approach. These works were selected for two reasons: (i) the  
authors created a template matching approach/module or have it as part of a full C-KBQA system; (ii) it is possible to retrain their  
approach with another dataset (open source code), or the authors also evaluated the results on LC-QuAD 2.0, even without using a  
preprocessed version of the dataset. The baselines are listed as follows.

- Dileep et al. (2021): In this paper, two machine learning models and three different preprocessing techniques  
    were used to generate results and identify the best model for template matching on LC-QuAD-2.0. The authors  
    presented that the XGBoost achieved good results in template matching.
- Athreya et al. (2021): This work also uses a Tree-LSTM, but on LC-QuAD 1.0. We retrained our model using the LC-  
    QuAD 1.0 to compare our system against theirs. LC-QuAD 1.0 (Trivedi et al., 2017) contains 5000 questions  
    composed of 5042 entities and 615 predicates. The questions were created from a list of template questions that  
    the work of Athreya et al. (2021) tries to predict what type of template a natural language question fits.

- Diomedi and Hogan (2021): This work adopts a neural machine translation (NMT) approach to translate a natural  
    language into a structured query language (templates). NMT is then used to create a query template with entity  
    placeholders, similar to our dummy answer template, but only performed for entities (subjects and objects).
- Evseev and Arkhipov (2020): This work performed the template matching step using a BERT classification and  
    Support Vector Machine to determine the SPARQL template type. The authors presented that the BERT  
    classification achieves the best template matching results.

The experiments were carried out on four datasets. First, we compare our approach to Dileep et al. (2021) and Diomedi and Hogan  
(2021) using LC-QuAD 2.1 and 29 target classes (templates). Next, we compare our approach to Evseev and Arkhipov (2020) using LC-  
QuAD 2.1 and 13 grouped target classes. The classes were grouped according to the protocol presented in Section 4 (see Table 1). LC-  
QuAD 1.0 was used to compare our approach to Athreya et al. (2021) using the same preprocessing performed by the authors, resulting  
in 15 target classes. Finally, we present the results using the WebQuestionsSP and ComplexWebQuestions using 13 and 16 templates  
respectively (see Section 4.1.2).

Table 3 presents the results, where “HTL” stands for our Tree-LSTM approach, “HTL-” stands for the HTL with the hereditary attention  
layer disabled, and “ _w/paraph_ ” represents the experiments using LC-QuAD 2.1 paraphrase questions as input. The experiments were  
evaluated using accuracy, and macro and weighted metrics: precision, recall, and f1-score. Some metrics are not available because the  
original paper did not provide these values, or we could not reproduce their results.

New approaches need to deal with biases better and not create brittle and spurious systems. Some C-KBQA systems are brittle because  
they are not robust enough yet and can fail to answer a question when just a few parts of the question are a little modified, even if the  
main meaning is preserved (Jia & Liang, 2017). Therefore, it is necessary to handle the dataset pre-processing step carefully, separate it  
with balanced training classes, and explore some question paraphrases to ensure that most types of questions are being explored. Our  
system was evaluated by adding the paraphrased questions in the training set of the LC-Quad 2.1 dataset to analyze the brittleness of  
the system.

The results in Table 3 show that our approach outperforms most of the baselines. HTL achieves good accuracy, precision, and recall.  
Furthermore, in most of the results HTL achieves better results than HTL- confirming that the attention model improves the standard  
Tree-LSTM. Regarding the LC-QuAD 2.1 with full template classification results, HTL achieved the best result with 73.3% of accuracy  
and more than 70% for precision, recall, and f1-score. This shows that HTL performs well even in this imbalanced scenario with  
multiple classes. When using the paraphrase questions, the results of HTL get even better, improving the metrics by more than 16 pp.  
Unlike the HTL training, it is worth noting that the works of Athreya et al., 2021, Dileep et al., 2021 and Evseev and Arkhipov (2020)  
made no use of a development set during the training step, and the hyperparameter tuning was performed on the testing set,  
according to their authors.

In Evseev and Arkhipov (2020), the authors have grouped templates into smaller groups to evaluate their approach. To compare our  
results with theirs, we used the LC-QuAD 2.1 with group classification. HTL achieved 85.5% accuracy during the group classification  
while the work of Evseev and Arkhipov (2020) achieved 90.8%. There are some points to observe when comparing our work  
with Evseev and Arkhipov (2020). Their template matching step is performed using a BERT, a fully connected attention mechanism.  
The training of these approaches can be computationally expensive and limit the amount of tuning done (Liu et al., 2019). Our  
approach is less expensive and can be easily specialized for other KB. Also, as the results were not publicly disclosed, we cannot assess  
the differences in the training/testing sets or the performance in the imbalanced scenario (regarding the precision, recall, and f1-score  
metrics). Besides, HTL overcomes the baseline work with 1.6 pp of accuracy when using the paraphrase questions.

When comparing to Athreya et al. (2021), HTL almost achieves the same results presented by the authors in the LC-QuAD 1 dataset.  
The authors used one-hot encoding of characters as additional input that helps the network to achieve better results. However, this  
additional feature can easily overfit the training and not generalize for characters that have not appeared before. In our HTL, the  
hereditary attention mechanism is used to assist the Tree-LSTM in detecting the most relevant information of a question. With HTL,  
we could achieve accuracy with only 1.1 pp smaller.

Regarding the WebQuestionsSP and ComplexWebQuestion datasets, both HTL- and HTL achieved better results than the approach of  
Athreya et al. (2021). However, HTL presented results slightly lower than HTL- (0.1 pp and 0.2 pp of accuracy). Many factors could  
cause these limitations. For example, both datasets are highly imbalanced, unlike the LC-QuAD dataset. Although these four datasets  
are suitable for C-KBQA systems evaluation, they differ on volume and balance of the data. For instance, WebQuestionsSP less than

5000 questions while ComplexWebQuestions and LC-Quad 2.0 contains more than 30,000 questions. Moreover, the 13 most frequent  
templates in the LC-QuAD 2.0 correspond to 79% of the questions, while in the ComplexWebQuestions the same proportion is reached  
by only three templates.

As discussed in Section 2 , the complex questions can be divided into two subgroups: multi-hop questions and constraint questions. In  
multi-hop questions, a C-KBQA system has to handle several subjects and predicates that can be found in the question (Li et al., 2020).  
In constraint questions, the NLQ often includes some restrictions that limit the answering options for a given question (Shin & Lee,  
2020 ). Those restrictions can be of several types, for example, temporal, ordinal, quantitative, and others, that modify the main  
subjects of an NLQ and consequently change the answer. Regarding the complex question match, HTL also has a great performance.  
We divided the question in LC-QuAD 2.1 into different types of natural language questions to illustrate this performance. Table 4  
presents the results of the template matching divided into four question types: Simple question, Constraint question, Multi-hop  
question, and both Multi-hop and Constraint at the same time. It is possible to see that HTL can achieve good results for all question  
types. HTL has a macro and weighted average for precision, recall, and F1-score greater than 80% for all the question types.

## 6. Final remarks

This work presented a new C-KBQA approach using a template matching approach. The C-KBQA approach combines Semantic Parsing  
and Neural Networks techniques to determine the answer templates that a complex question fits. A Tree-LSTM is used to analyze the  
structured semantic information of a question correctly. An attention mechanism was created to assist the Tree-LSTM in selecting the  
most important information. In the so-called Hereditary Tree-LSTM (HTL), each neural network cell inherits the attention from  
another neural network cell in a bottom-up way.

We presented the inconsistencies in some datasets, e.g., question duplication, and all the steps to create the answer templates used in  
this work. In addition, a new cleaned version of LC-QuAD 2.0, the so-called LC-QuAD 2.1, was released. The LC-QuAD 2.1 is available for  
further research and was used to evaluate most of the baselines used to compare our C-KBQA approach. The results show that our HTL  
can overcome most of the baselines in the template matching step. Also, we presented that some C-KBQA systems have to explore  
some question paraphrases to ensure that most types of questions are being explored. As a result, these systems can fail to answer a  
question when just a few parts of the question are a little modified, even if the main meaning is preserved.

There are still some challenges and limitations. KBQA systems are KB-dependent, and it is necessary to ensure that the KB structure is  
up-to-date with the templates used in the training step. Since the evaluation dataset is created at a fixed KB version, the system learns  
to answer the question related to the training dataset. The answer templates were based on SPARQL 1.0; however, a new version of  
SPARQL 1.1 was already released. With the advances in the query language, the templates must follow these updates and be constantly  
updated to answer real questions. Also, the biggest mistake of the HTL is to differentiate templates with 2 and 3 hops. These errors  
occur as the KB schema was not included as inputs during the Hereditary Tree-LSTM training.

The use of the HTL still needs to be further investigated, and additional information may improve the accuracy of the approach. For  
example, including the KB schema information on training can create more accurate results and need to be evaluated in future work.  
Also, using Named Entity Recognition and Disambiguation and relation recognition methods to detect KB entities/relations and  
measure the distance between them can improve the results of our template matching. Furthermore, exploring HTL for other  
semantic tasks such as sentiment classification and semantic relatedness may also archive good results. Finally, evaluating HTL as part  
of a complete C-KBQA system still has to be evaluated.

## CRediT authorship contribution statement

**Jorão Gomes Jr.:** Conceptualization, Methodology, Software, Writing – original draft. **Rômulo Chrispim de Mello:** Data acquisition,  
Data curation. **Victor Ströele:** Writing – review & editing, Supervision. **Jairo Francisco de Souza:** Writing – review & editing,  
Supervision.

## Declaration of Competing Interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to  
influence the work reported in this paper.

## Acknowledgments

The authors thank the financial support provided. This study was financed in part by the Coordenação de Aperfeiçoamento de Pessoal  
de Nível Superior — Brazil (CAPES) Finance Code 001. Also, the authors thank the financial support of the National Education and  
Research Network (RNP). This work was supported by UFJF’s High-Speed Integrated Research Network (RePesq).  
https://www.repesq.ufjf.br. All authors have checked the manuscript and have agreed to the submission.

## Appendix.

This appendix section present the preprocessing and dummy template creation results on the Lc-QuAD 2.1. The results for DBpedia  
2018 are presented in Table 5. Read GID as group ID, TID as template ID, #Q as the number of questions in the template ID, and #TQ as  
the number of questions in the group when reading the columns names.
