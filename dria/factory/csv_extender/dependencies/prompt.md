Analyze the CSV data and output the overall column dependency hierarchy using '->' to show relationships.

Example:

```
column 1 -> independent
column 2 -> column 1
column 4 -> column 1
column 3 -> column 2, column 4
```



Here is the sample data:
<sample_data>
{{csv}}
</sample_data>

Output the only dependencies without comments.
Output: