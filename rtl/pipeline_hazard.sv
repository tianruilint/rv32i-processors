module pipeline_hazard (
    input logic id_valid,
    input logic [4:0] id_rs1_addr,
    input logic [4:0] id_rs2_addr,
    input logic id_uses_rs1,
    input logic id_uses_rs2,
    input logic ex_valid,
    input logic ex_reg_write,
    input logic [1:0] ex_result_src,
    input logic [4:0] ex_rd_addr,
    input logic redirect,
    output logic stall,
    output logic bubble,
    output logic flush
);

logic load_use;

assign load_use = id_valid && ex_valid && ex_reg_write &&
                  ex_result_src == 2'b01 && ex_rd_addr != 5'd0 &&
                  ((id_uses_rs1 && id_rs1_addr == ex_rd_addr) ||
                   (id_uses_rs2 && id_rs2_addr == ex_rd_addr));

assign flush = redirect;
assign stall = load_use && !redirect;
assign bubble = stall;

endmodule
