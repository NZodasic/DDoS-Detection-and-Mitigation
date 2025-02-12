# DDoS DeepLearning Approach - Cyber Security Project


## Team member

Name | Student ID | Role
:--:|:--:|:--:
Nguyễn Võ Chí Dũng | 23560012 | Leader - Deploy
Nguyễn Hoàng Phương Uyên | 23560090 | Research Solution
Nguyễn Việt An | 23560092 | Data Preprocessing - Model Optimal


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

#Mã xử lý:

#Lưu lượng CIC DDoS 2019: `data_loaders.CIC_DDoS_2019`
#Lưu lượng ngoài: `data_loaders.Generic_Pcap_Dataset`

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

Quy trình đào tạo sử dụng `Project-CS-P-Final.ipynb`:

1. Tải 10.000 gói tấn công từ CIC-DDoS2019.
2. Ghi và nhập 10.000 gói lưu lượng thông thường.
3. Huấn luyện với Trainer đơn giản.

```
Epoch 1/10, Loss: 0.0037, Train Accuracy: 0.9995, Test Accuracy: 0.9996
Epoch 2/10, Loss: 0.0030, Train Accuracy: 0.9996, Test Accuracy: 0.9996
Epoch 3/10, Loss: 0.0030, Train Accuracy: 0.9996, Test Accuracy: 0.9996
Epoch 4/10, Loss: 0.0030, Train Accuracy: 0.9996, Test Accuracy: 0.9996
Epoch 5/10, Loss: 0.0031, Train Accuracy: 0.9996, Test Accuracy: 0.9996
Epoch 6/10, Loss: 0.0029, Train Accuracy: 0.9996, Test Accuracy: 0.9996
Epoch 7/10, Loss: 0.0029, Train Accuracy: 0.9996, Test Accuracy: 0.9996
Epoch 8/10, Loss: 0.0029, Train Accuracy: 0.9996, Test Accuracy: 0.9996
Epoch 9/10, Loss: 0.0029, Train Accuracy: 0.9996, Test Accuracy: 0.9996
Epoch 10/10, Loss: 0.0029, Train Accuracy: 0.9996, Test Accuracy: 0.9996

Full model has been saved successfully!
Full model has been loaded successfully!
<ipython-input-30-e36e4e49294e>:7: FutureWarning: You are using `torch.load` with `weights_only=False` (the current default value), which uses the default pickle module implicitly. It is possible to construct malicious pickle data which will execute arbitrary code during unpickling (See https://github.com/pytorch/pytorch/blob/main/SECURITY.md#untrusted-models for more details). In a future release, the default value for `weights_only` will be flipped to `True`. This limits the functions that could be executed during unpickling. Arbitrary objects will no longer be allowed to be loaded via this mode unless they are explicitly allowlisted by the user via `torch.serialization.add_safe_globals`. We recommend you start setting `weights_only=True` for any use case where you don't have full control of the loaded file. Please open an issue on GitHub for any issues related to this experimental feature.
  model = torch.load("ddos_model_full.pt")
```

Quy trình dự đoán ghi nhận gói từ thiết bị mạng (chỉnh tham số INTERFACE) và ước tính tỷ lệ tấn công. 

```
----- Benign -----
Predictions: [[0]
 [0]
 [0]
 ...
 [0]
 [0]
 [0]]

----- Attack -----
Predictions: [[1]
 [1]
 [1]
 ...
 [1]
 [1]
 [1]]
```

## Result
![image](https://github.com/user-attachments/assets/4640ffd6-2de4-4eca-8ad7-3d8693fd54ff)
![image](https://github.com/user-attachments/assets/1ca16f63-97d7-401f-845d-20cc0de2c3f4)

