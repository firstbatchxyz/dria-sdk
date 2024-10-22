Your task is to diversify given data by generating new examples for independent columns.
Independent columns are {{independent_columns}}.

Here is the sample data:
<sample_data>
{{csv}}
</sample_data>

After you output hierarchy, generate new examples ONLY for independent columns. Make sure your examples are rich and fit in the distribution of the original column in data.
Your examples should NOT include already existing values in sample data. Be creative and analytical. 
First reason about how you should diversify examples and output your new data in JSON

Example:

```json
{
"column 1": ["new example", "new example", ...],
"column 2": ["new example", "new example", ...],
}
```

Output: