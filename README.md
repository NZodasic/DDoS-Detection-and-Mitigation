# DDoS DeepLearning Approach

Nhận dạng luồng DDoS bằng mô hình học sâu.

## Model

Việc thu thập thông tin thống kê toàn bộ luồng trong môi trường thực tế là không khả thi. Em áp dụng mô hình mạng nơ-ron tích chập (CNN) được tham khảo từ LUCID: A Practical Lightweight Deep Learning Solution for DDoS Detection. Các gói dữ liệu được trích xuất trong một khoảng thời gian cố định để làm đầu vào.

```
Model: "CNNModel"
============================================================================================================================================
Layer (type:depth-idx)                   Input Shape               Output Shape              Param #                   Trainable
============================================================================================================================================
CNN                                      [64, 1, 100]              [64, 1]                   --                        True
├─Conv1d: 1-1                            [64, 1, 100]              [64, 16, 100]             64                        True
├─MaxPool1d: 1-2                         [64, 16, 100]             [64, 16, 50]              --                        --
├─Conv1d: 1-3                            [64, 16, 50]              [64, 32, 50]              1,568                     True
├─MaxPool1d: 1-4                         [64, 32, 50]              [64, 32, 25]              --                        --
├─Linear: 1-5                            [64, 800]                 [64, 128]                 102,528                   True
├─Linear: 1-6                            [64, 128]                 [64, 1]                   129                       True
├─Sigmoid: 1-7                           [64, 1]                   [64, 1]                   --                        --
============================================================================================================================================
Total params: 104,289
Trainable params: 104,289
Non-trainable params: 0
Total mult-adds (M): 12.00
============================================================================================================================================
Input size (MB): 0.03
Forward/backward pass size (MB): 1.70
Params size (MB): 0.42
Estimated Total Size (MB): 2.15
============================================================================================================================================
```

## Dữ liệu CIC-DDoS2019

Tập dữ liệu hiện được chọn [Tập dữ liệu CIC DDoS 2019](https://www.unb.ca/cic/datasets/ddos-2019.html).

Sử dụng CIC DDoS 2019 Dataset, với lưu lượng tấn công phong phú nhưng thiếu lưu lượng thông thường. Để bổ sung, lưu lượng thông thường được ghi lại thủ công và nhập qua tham số `pcap_file_list`.

Mã xử lý:

Lưu lượng CIC DDoS 2019: `data_loaders.CIC_DDoS_2019`
Lưu lượng ngoài: `data_loaders.Generic_Pcap_Dataset`

### Đặc trưng và chuẩn hóa

Các đặc trưng loại trừ thông tin IP/cổng, chỉ dựa vào nội dung gói. Toàn bộ 160 bit được chuẩn hóa thành phân phối [0, 1].

<!-- | Loại đặc trưng     | Chuẩn hóa                                                       | Miêu tả                                                         |
| ------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Time         | Nhân 1,000,000, chuyển nhị phân 32 bit | Khoảng cách từ gói đầu tiên |
| PKT Len      | Nhị phân 16 bit. | Chiều dài gói |
| IP/TCP Flags     | Nhị phân 8/16/32 bit | Giá trị đặc trưng tương ứng |
| Protocols    | Nhị phân 8 bit | Loại giao thức | -->

|Loại đặc trưng | Phương pháp chuẩn hóa | Mô tả |
| ------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Time | Nhân với 1.000.000, chuyển đổi thành nhị phân 32 bit và chuẩn hóa thành số dấu phẩy động 32 bit. |Khoảng thời gian từ gói hiện tại đến gói đầu tiên trong luồng. Gói đầu tiên là 0.|
| Chiều dài gói (PKT Len) | Nhị phân 16 bit, chuẩn hóa thành số dấu phẩy động. Cắt bớt nếu vượt giới hạn, gán giá trị 1 cho toàn bộ 16 bit. | Dựa trên chiều dài của gói.|
| Cờ IP (IP Flags) | Nhị phân 16 bit, chuẩn hóa thành số dấu phẩy động. | Không cần cắt bớt, do giá trị nằm trong phạm vi cố định.|
| Protocol | Nhị phân 8 bit, chuẩn hóa thành số dấu phẩy động. | Giá trị tương ứng với giao thức của thông điệp IP.|
| Chiều dài TCP (TCP Len) | Nhị phân 16 bit, chuẩn hóa thành số dấu phẩy động. | Xác định kích thước dữ liệu TCP.|
| TCP ACK | Nhị phân 32 bit, chuẩn hóa thành số dấu phẩy động. | Giá trị ACK trong giao thức TCP.|
| Cờ TCP (TCP Flags) | Nhị phân 8 bit, chuẩn hóa thành số dấu phẩy động. | Xác định trạng thái của kết nối TCP.|
| Kích thước cửa sổ TCP (TCP win size) | Nhị phân 16 bit, chuẩn hóa thành số dấu phẩy động. | Kích thước cửa sổ TCP.|
| Chiều dài UDP (UDP Len) | Nhị phân 16 bit, chuẩn hóa thành số dấu phẩy động. | Kích thước của gói UDP.|


Các đặc trưng trên có tổng cộng 160 bit. Tham số này cần phải tương ứng với hình dạng của mô hình được sử dụng trong quá trình đào tạo.

## Training và Predict

Quy trình đào tạo sử dụng `experiments.dcnn_on_cic_ddos_2019`:

1. Tải 10.000 gói tấn công từ CIC-DDoS2019.
2. Ghi và nhập 10.000 gói lưu lượng thông thường.
3. Huấn luyện với Trainer đơn giản.

```
WARNING:__main__:Programme started in train mode!
INFO:__main__:Loading normal flow...
100%|████████████████████████████████████████| 4/4 [00:53<00:00, 13.36s/it, Loaded flow number=1e+4]
INFO:__main__:Loading attack flow...
INFO:templates.utils:Cache is loaded from cache/generic_loader/7-28T05-02/label_from_csv_cache
100%|██████████████████████████████████| 30/30 [00:09<00:00,  3.19it/s, BENIGN=0, MSSQL=0, UDP=1e+4]
INFO:root:Generating dataset...
100%|███████████████████████████████████████████████████| 183227/183227 [00:00<00:00, 919449.29it/s]
INFO:templates.utils:Cache is saved to cache/generic_loader/7-28T05-02/combine_set_cache
INFO:templates.utils:Cache is loaded from cache/generic_loader/7-28T05-02/combine_set_cache
Epoch 1/2
INFO:templates.utils:Cache is loaded from cache/generic_loader/7-28T05-02/combine_set_cache
2000/2000 [==============================] - 29s 14ms/step - loss: 0.1175 - categorical_accuracy: 0.9808 - categorical_crossentropy: 0.1175
Epoch 2/2
INFO:templates.utils:Cache is loaded from cache/generic_loader/7-28T05-02/combine_set_cache
2000/2000 [==============================] - 28s 14ms/step - loss: 0.0344 - categorical_accuracy: 0.9960 - categorical_crossentropy: 0.0344
INFO:__main__:Saving weight...
```

Quy trình dự đoán ghi nhận gói từ thiết bị mạng (chỉnh tham số INTERFACE) và ước tính tỷ lệ tấn công. 

```
WARNING:__main__:Programme started in predict mode!
INFO:__main__:Start capture and predict...
INFO:__main__:Predict turn 1
INFO:__main__:Capturing...
INFO:__main__:Capture done, generating predict set...
100%|████████████████████████████████████████| 1/1 [00:02<00:00,  2.50s/it, Loaded flow number=3943]
100%|██████████████████████████████████████████████████████| 9730/9730 [00:00<00:00, 1324373.78it/s]
INFO:templates.utils:Cache is saved to cache/generic_loader/7-28T05-02/combine_set_cache(predict)
INFO:templates.utils:Cache is loaded from cache/generic_loader/7-28T05-02/combine_set_cache(predict)
WARNING:__main__:Attack: about 96%
INFO:__main__:Predict turn 2
INFO:__main__:Capturing...
INFO:__main__:Capture done, generating predict set...
100%|█████████████████████████████████████████| 1/1 [00:03<00:00,  3.12s/it, Loaded flow number=274]
100%|███████████████████████████████████████████████████████| 1970/1970 [00:00<00:00, 533633.36it/s]
INFO:templates.utils:Cache is saved to cache/generic_loader/7-28T05-02/combine_set_cache(predict)
INFO:templates.utils:Cache is loaded from cache/generic_loader/7-28T05-02/combine_set_cache(predict)
WARNING:__main__:Attack: about 1%
```

