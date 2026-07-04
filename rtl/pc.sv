module pc (
    input  logic        clk,
    input  logic        reset,
    input  logic        take_target,
    input  logic [31:0] target_pc,
    output logic [31:0] current_pc
);

logic [31:0] next_pc;

always_comb begin
    if (take_target)
        next_pc = target_pc;
    else
        next_pc = current_pc + 32'd4;
end

always_ff @(posedge clk) begin
    if (reset)
        current_pc <= 32'b0;
    else
        current_pc <= next_pc;
end

endmodule
