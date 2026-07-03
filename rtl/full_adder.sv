module full_adder (
    input  a_i, b_i, cin_i, 
    output sum_o, cout_o 
);
    assign {cout_o, sum_o} = a_i + b_i + cin_i;
endmodule
