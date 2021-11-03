This folder contains all the data compiled for the study, organized in CSV (comma-separated values) files.
The individual files are structured as follows:

* [languages.csv](languages.csv): List of languages
	* `ID`: a three- (attested) or four-letter (reconstructed) string
	* `Name`: the name as used in the paper
	* `Glottocode`: the identified used in [Glottolog](https://www.glottolog.org)
	* `Longitude`: longitude, decimal format
	* `Latitude`: latitude, decimal format
* [inflection_data.csv](inflection_data.csv): Prefix-Verb combinations for various inflected verbs. The central source of information about what extensions affected what verbs.
	* `Meaning_ID`: a reference to the values of [cognate_sets.csv](cognate_sets.csv):`Meaning_ID`
	* `Verb_Cognateset_ID`: [cognate_sets.csv](cognate_sets.csv):`ID
`+[cognate_sets.csv](cognate_sets.csv):`ID`
	* `Language_ID`: 
	* `Inflection`: 
	* `Form`: 
	* `Prefix_Cognateset_ID`: 
	* `Source`: 
	* `Full_Form`: 
	* `Comment`: 

* [link](#foo)
* [extensions.csv](extensions.csv): List of incomplete first person marker extensions with language and cognate set ID.
* [verb_stem_data.csv](verb_stem_data.csv): Verbs roots or stems of verbs reconstructed in the manuscript.
* [cognate_sets.csv](cognate_sets.csv): Reconstructed Proto-Cariban forms of verbal prefixes and stems.
* [examples.csv](examples.csv): Illustrative example sentences used in the manuscript.
* [cldf](cldf): dataset in the CLDF format
* [bathe_data.csv](bathe_data.csv): Intransitive and transitive forms of 'to bathe' from various languages.
* [split_s_data.csv](split_s_data.csv): Additional data illustrating non-person-based properties of the split-S system in languages across the family, reconstructible to Proto-Cariban.