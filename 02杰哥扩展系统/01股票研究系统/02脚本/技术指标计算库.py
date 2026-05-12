# ============================================================
# 脚本名称：技术指标计算库.py
# 所属系统：02杰哥扩展系统/01股票研究系统/02脚本
# 功能描述：提供所有公认技术指标的计算函数
# 创建日期：2026-05-10
# 适用范围：股票系统所有分析、识别、筛选脚本
# 依赖：pandas, numpy
# ============================================================

import pandas as pd
import numpy as np


def _safe_denominator(series):
    """把0替换为NaN，避免除零导致无穷值污染后续评分。"""
    return series.replace(0, np.nan)

# ============================================================
# 一、趋势类指标
# ============================================================

def calc_ma(df, periods=[5, 10, 20, 30, 60, 120, 250]):
    """移动平均线"""
    for p in periods:
        df[f'MA{p}'] = df['收盘'].rolling(window=p).mean()
    return df

def calc_ema(df, periods=[5, 10, 20, 60]):
    """指数移动平均线"""
    for p in periods:
        df[f'EMA{p}'] = df['收盘'].ewm(span=p, adjust=False).mean()
    return df

def calc_macd(df, short=12, long=26, mid=9):
    """MACD指标"""
    df['EMA12'] = df['收盘'].ewm(span=short, adjust=False).mean()
    df['EMA26'] = df['收盘'].ewm(span=long, adjust=False).mean()
    df['DIF'] = df['EMA12'] - df['EMA26']
    df['DEA'] = df['DIF'].ewm(span=mid, adjust=False).mean()
    df['MACD'] = 2 * (df['DIF'] - df['DEA'])
    return df

def calc_boll(df, n=20):
    """布林带"""
    df['BOLL_MA'] = df['收盘'].rolling(window=n).mean()
    df['BOLL_STD'] = df['收盘'].rolling(window=n).std()
    df['BOLL_UP'] = df['BOLL_MA'] + 2 * df['BOLL_STD']
    df['BOLL_DN'] = df['BOLL_MA'] - 2 * df['BOLL_STD']
    df['BOLL_WIDTH'] = (df['BOLL_UP'] - df['BOLL_DN']) / df['BOLL_MA'] * 100
    return df

def calc_envelope(df, n=20, pct=3):
    """价格包络线"""
    ma = df['收盘'].rolling(window=n).mean()
    df[f'ENV_UP'] = ma * (1 + pct/100)
    df[f'ENV_DN'] = ma * (1 - pct/100)
    return df

# ============================================================
# 二、动量类指标
# ============================================================

def calc_rsi(df, periods=[6, 12, 24]):
    """RSI相对强弱指标"""
    for p in periods:
        delta = df['收盘'].diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        avg_gain = gain.rolling(window=p).mean()
        avg_loss = loss.rolling(window=p).mean()
        rs = avg_gain / avg_loss
        df[f'RSI{p}'] = 100 - (100 / (1 + rs))
    return df

def calc_kdj(df, n=9, m1=3, m2=3):
    """KDJ随机指标"""
    low = df['最低'].rolling(window=n).min()
    high = df['最高'].rolling(window=n).max()
    rsv = (df['收盘'] - low) / _safe_denominator(high - low) * 100
    rsv = rsv.fillna(50)
    k = rsv.ewm(com=m1-1, adjust=False).mean()
    d = k.ewm(com=m2-1, adjust=False).mean()
    j = 3 * k - 2 * d
    df['KDJ_K'] = k
    df['KDJ_D'] = d
    df['KDJ_J'] = j
    return df

def calc_wr(df, n=14):
    """威廉指标WR"""
    high_n = df['最高'].rolling(window=n).max()
    low_n = df['最低'].rolling(window=n).min()
    df[f'WR{n}'] = (high_n - df['收盘']) / _safe_denominator(high_n - low_n) * 100
    return df

def calc_cci(df, n=14):
    """CCI商品通道指数"""
    tp = (df['最高'] + df['最低'] + df['收盘']) / 3
    ma = tp.rolling(window=n).mean()
    md = tp.rolling(window=n).apply(lambda x: np.abs(x - x.mean()).mean())
    df['CCI'] = (tp - ma) / (0.015 * md)
    return df

def calc_mtm(df, n=12):
    """MTM动量指标"""
    df[f'MTM{n}'] = df['收盘'] - df['收盘'].shift(n)
    return df

def calc_roc(df, n=12):
    """ROC变动率指标"""
    df[f'ROC{n}'] = (df['收盘'] - df['收盘'].shift(n)) / df['收盘'].shift(n) * 100
    return df

# ============================================================
# 三、波动性指标
# ============================================================

def calc_atr(df, n=14):
    """ATR平均真实波幅"""
    high_low = df['最高'] - df['最低']
    high_close = (df['最高'] - df['收盘'].shift()).abs()
    low_close = (df['最低'] - df['收盘'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=n).mean()
    return df

def calc_amplitude(df):
    """振幅"""
    if '振幅' not in df.columns:
        df['振幅'] = (df['最高'] - df['最低']) / _safe_denominator(df['收盘'].shift(1)) * 100
    return df

def calc_std(df, n=20):
    """标准差"""
    df[f'STD{n}'] = df['收盘'].rolling(window=n).std()
    return df

# ============================================================
# 四、成交量与资金类指标
# ============================================================

def calc_volume_ma(df, periods=[5, 10, 20]):
    """成交量均线"""
    for p in periods:
        df[f'VOL_MA{p}'] = df['成交量'].rolling(window=p).mean()
        df[f'成交量MA{p}'] = df[f'VOL_MA{p}']
    return df

def calc_amount_ma(df, periods=[5, 10, 20]):
    """成交额均线"""
    if '成交额' not in df.columns:
        return df
    for p in periods:
        df[f'成交额MA{p}'] = df['成交额'].rolling(window=p).mean()
    return df

def calc_volume_ratio(df, n=5):
    """量比：当日成交量 / 前N日平均成交量。"""
    avg_volume = df['成交量'].rolling(window=n).mean().shift(1)
    df['量比'] = df['成交量'] / _safe_denominator(avg_volume)
    df[f'量比{n}日'] = df['量比']
    return df

def calc_vr(df, n=26):
    """VR容量比率"""
    av = df.apply(lambda x: x['成交量'] if x['收盘'] > x['开盘'] else 0, axis=1).rolling(window=n).sum()
    bv = df.apply(lambda x: x['成交量'] if x['收盘'] < x['开盘'] else 0, axis=1).rolling(window=n).sum()
    cv = df.apply(lambda x: x['成交量'] if x['收盘'] == x['开盘'] else 0, axis=1).rolling(window=n).sum()
    df['VR'] = (av + 0.5 * cv) / (bv + 0.5 * cv) * 100
    return df

def calc_obv(df):
    """OBV能量潮"""
    obv = [0]
    for i in range(1, len(df)):
        if df['收盘'].iloc[i] > df['收盘'].iloc[i-1]:
            obv.append(obv[-1] + df['成交量'].iloc[i])
        elif df['收盘'].iloc[i] < df['收盘'].iloc[i-1]:
            obv.append(obv[-1] - df['成交量'].iloc[i])
        else:
            obv.append(obv[-1])
    df['OBV'] = obv
    return df

def calc_turnover_rate(df):
    """换手率（成交量/流通股本）"""
    if '换手率' in df.columns:
        return df
    if '流通股本' in df.columns:
        df['换手率'] = df['成交量'] / df['流通股本'] * 100
    else:
        df['换手率'] = np.nan  # 等待后续补入流通股本数据，不能用0伪装真实值。
    return df

# ============================================================
# 五、形态类指标
# ============================================================

def calc_gap(df):
    """缺口"""
    df['缺口'] = (df['开盘'] - df['收盘'].shift(1)) / _safe_denominator(df['收盘'].shift(1)) * 100
    return df

def calc_high_low_open(df):
    """高低开"""
    df['高低开'] = (df['开盘'] - df['收盘'].shift(1)) / _safe_denominator(df['收盘'].shift(1)) * 100
    return df

def calc_new_high(df, n=20):
    """N日新高"""
    df[f'新高{n}'] = df['最高'].rolling(window=n).max()
    df[f'是新高{n}'] = (df['最高'] == df[f'新高{n}']).astype(int)
    return df

def calc_new_low(df, n=20):
    """N日新低"""
    df[f'新低{n}'] = df['最低'].rolling(window=n).min()
    df[f'是新低{n}'] = (df['最低'] == df[f'新低{n}']).astype(int)
    return df

def calc_breakthrough_pullback(df, n=20):
    """突破回踩"""
    df['N日新高'] = df['最高'].rolling(window=n).max()
    df['突破'] = (df['最高'] == df['N日新高']).astype(int)
    df['回踩'] = ((df['最低'] - df['MA20']).abs() / df['MA20'] < 0.02).astype(int)
    return df

def calc_limit_status(df):
    """涨跌停与情绪近似字段；不替代交易所精确涨跌停规则，用于市场情绪粗筛。"""
    if '涨跌幅' not in df.columns:
        df['涨跌幅'] = (df['收盘'] - df['收盘'].shift(1)) / _safe_denominator(df['收盘'].shift(1)) * 100
    df['近似涨停'] = (df['涨跌幅'] >= 9.8).astype(int)
    df['近似跌停'] = (df['涨跌幅'] <= -9.8).astype(int)
    df['强势大阳'] = ((df['涨跌幅'] >= 5) & (df['收盘'] > df['开盘'])).astype(int)
    df['弱势大阴'] = ((df['涨跌幅'] <= -5) & (df['收盘'] < df['开盘'])).astype(int)
    df['连涨天数'] = df['涨跌幅'].gt(0).astype(int).groupby(df['涨跌幅'].le(0).cumsum()).cumsum()
    df['连跌天数'] = df['涨跌幅'].lt(0).astype(int).groupby(df['涨跌幅'].ge(0).cumsum()).cumsum()
    df['连板近似天数'] = df['近似涨停'].groupby(df['近似涨停'].eq(0).cumsum()).cumsum()
    return df

def calc_box_breakout(df, n=60, tolerance=0.03):
    """箱体与平台突破：借鉴成熟软件的形态入口，采用可解释的自有规则。"""
    box_high = df['最高'].rolling(window=n).max().shift(1)
    box_low = df['最低'].rolling(window=n).min().shift(1)
    box_mid = (box_high + box_low) / 2
    df[f'{n}日箱体上沿'] = box_high
    df[f'{n}日箱体下沿'] = box_low
    df[f'{n}日箱体宽度'] = (box_high - box_low) / _safe_denominator(box_mid) * 100
    df[f'{n}日箱体突破'] = (df['收盘'] > box_high * (1 + tolerance)).astype(int)
    df[f'{n}日箱体内整理'] = (
        (df['收盘'] <= box_high * (1 + tolerance)) &
        (df['收盘'] >= box_low * (1 - tolerance))
    ).astype(int)
    return df

def calc_vcp_contraction(df, windows=[20, 40, 60]):
    """VCP波动收缩代理：观察价格振幅与成交额波动是否逐步收敛。"""
    width_cols = []
    amount_vol_cols = []
    for w in windows:
        high = df['最高'].rolling(window=w).max()
        low = df['最低'].rolling(window=w).min()
        mid = (high + low) / 2
        width_col = f'{w}日价格区间宽度'
        df[width_col] = (high - low) / _safe_denominator(mid) * 100
        width_cols.append(width_col)
        if '成交额' in df.columns:
            amount_col = f'{w}日成交额波动率'
            df[amount_col] = df['成交额'].rolling(window=w).std() / _safe_denominator(df['成交额'].rolling(window=w).mean())
            amount_vol_cols.append(amount_col)
    if len(width_cols) >= 3:
        df['VCP价格收缩'] = (
            (df[width_cols[0]] < df[width_cols[1]]) &
            (df[width_cols[1]] < df[width_cols[2]])
        ).astype(int)
    if len(amount_vol_cols) >= 3:
        df['VCP量能收缩'] = (
            (df[amount_vol_cols[0]] < df[amount_vol_cols[1]]) &
            (df[amount_vol_cols[1]] < df[amount_vol_cols[2]])
        ).astype(int)
    price_flag = df['VCP价格收缩'] if 'VCP价格收缩' in df.columns else pd.Series(0, index=df.index)
    volume_flag = df['VCP量能收缩'] if 'VCP量能收缩' in df.columns else pd.Series(0, index=df.index)
    df['VCP收缩形态'] = ((price_flag == 1) & (volume_flag == 1)).astype(int)
    return df

# ============================================================
# 六、趋势强度类指标
# ============================================================

def calc_dmi(df, n=14):
    """DMI趋向指标"""
    up_move = df['最高'] - df['最高'].shift(1)
    down_move = df['最低'].shift(1) - df['最低']
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    tr = pd.concat([df['最高'] - df['最低'], 
                    (df['最高'] - df['收盘'].shift()).abs(), 
                    (df['最低'] - df['收盘'].shift()).abs()], axis=1).max(axis=1)
    atr = pd.Series(tr, index=df.index).rolling(window=n).mean()
    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)
    plus_di = plus_dm.rolling(window=n).mean() / _safe_denominator(atr) * 100
    minus_di = minus_dm.rolling(window=n).mean() / _safe_denominator(atr) * 100
    dx = (plus_di - minus_di).abs() / _safe_denominator(plus_di + minus_di) * 100
    df['PDI'] = plus_di
    df['MDI'] = minus_di
    df['ADX'] = dx.rolling(window=n).mean()
    df['ADXR'] = (df['ADX'] + df['ADX'].shift(n)) / 2
    return df

def calc_bias(df, n=6):
    """BIAS乖离率"""
    ma = df['收盘'].rolling(window=n).mean()
    df[f'BIAS{n}'] = (df['收盘'] - ma) / _safe_denominator(ma) * 100
    return df

def calc_ma_slope(df, periods=[20, 60, 120, 250], lookback=20):
    """均线方向与斜率，用于趋势阶段和米勒维尼类模板判断。"""
    for p in periods:
        ma_col = f'MA{p}'
        if ma_col not in df.columns:
            df[ma_col] = df['收盘'].rolling(window=p).mean()
        df[f'{ma_col}斜率{lookback}日'] = (df[ma_col] - df[ma_col].shift(lookback)) / _safe_denominator(df[ma_col].shift(lookback)) * 100
        df[f'{ma_col}向上'] = (df[f'{ma_col}斜率{lookback}日'] > 0).astype(int)
    return df

def calc_stage2_template(df):
    """第二阶段趋势模板代理；用于强趋势候选过滤，不直接等同买卖建议。"""
    if 'MA60' not in df.columns or 'MA120' not in df.columns or 'MA250' not in df.columns:
        df = calc_ma(df)
    if 'MA250向上' not in df.columns:
        df = calc_ma_slope(df)
    low_250 = df['最低'].rolling(window=250).min()
    high_250 = df['最高'].rolling(window=250).max()
    df['距250日低点涨幅'] = (df['收盘'] - low_250) / _safe_denominator(low_250) * 100
    df['收盘处于250日高点比例'] = df['收盘'] / _safe_denominator(high_250)
    conditions = [
        df['收盘'] > df['MA120'],
        df['收盘'] > df['MA250'],
        df['MA120'] > df['MA250'],
        df['MA250向上'] == 1,
        df['MA60'] > df['MA120'],
        df['MA60'] > df['MA250'],
        df['收盘'] > df['MA60'],
        df['距250日低点涨幅'] >= 30,
        df['收盘处于250日高点比例'] >= 0.75,
    ]
    score = sum(condition.astype(int) for condition in conditions)
    df['第二阶段模板得分'] = score
    df['第二阶段趋势模板'] = (score >= 8).astype(int)
    return df

def calc_period_returns(df, periods=[20, 60, 120, 250]):
    """多周期涨跌幅，作为强势样本识别和相似度评分的基础字段。"""
    for p in periods:
        df[f'{p}日涨跌幅'] = (df['收盘'] - df['收盘'].shift(p)) / _safe_denominator(df['收盘'].shift(p)) * 100
    return df

def calc_three_year_return(df, trading_days=750):
    """近三年涨跌幅；数据不足时记录可得区间涨跌幅并标记完整性。"""
    if len(df) > trading_days:
        base = df['收盘'].shift(trading_days)
        df['近三年涨跌幅'] = (df['收盘'] - base) / _safe_denominator(base) * 100
        df['近三年数据完整'] = True
    else:
        first_close = df['收盘'].iloc[0] if len(df) else np.nan
        df['近三年涨跌幅'] = (df['收盘'] - first_close) / first_close * 100 if first_close else np.nan
        df['近三年数据完整'] = False
    df['近三年可得涨跌幅'] = df['近三年涨跌幅']
    return df

def calc_drawdown(df):
    """当前回撤与历史最大回撤。"""
    peak = df['收盘'].cummax()
    df['当前回撤'] = (df['收盘'] - peak) / _safe_denominator(peak) * 100
    df['最大回撤'] = df['当前回撤'].cummin()
    return df

def calc_activity_metrics(df):
    """成交活跃与拥挤度代理，用于突破确认和高拥挤预警。"""
    if '成交额' in df.columns:
        df['成交额5_20比'] = df['成交额'].rolling(5).mean() / _safe_denominator(df['成交额'].rolling(20).mean())
        df['成交额20_60比'] = df['成交额'].rolling(20).mean() / _safe_denominator(df['成交额'].rolling(60).mean())
        df['成交额60日波动率'] = df['成交额'].rolling(60).std() / _safe_denominator(df['成交额'].rolling(60).mean())
    df['成交量5_20比'] = df['成交量'].rolling(5).mean() / _safe_denominator(df['成交量'].rolling(20).mean())
    df['成交量20_60比'] = df['成交量'].rolling(20).mean() / _safe_denominator(df['成交量'].rolling(60).mean())
    df['成交量60日波动率'] = df['成交量'].rolling(60).std() / _safe_denominator(df['成交量'].rolling(60).mean())
    if '换手率' in df.columns:
        df['换手率20_60比'] = df['换手率'].rolling(20).mean() / _safe_denominator(df['换手率'].rolling(60).mean())
        df['高拥挤预警'] = (df['换手率20_60比'] >= 2).astype(int)
    return df

# ============================================================
# 七、综合计算入口（一次计算所有指标）
# ============================================================

def calc_all_indicators(df):
    """一次性计算所有公认技术指标"""
    df = calc_ma(df)
    df = calc_ema(df)
    df = calc_macd(df)
    df = calc_boll(df)
    df = calc_envelope(df)
    df = calc_rsi(df)
    df = calc_kdj(df)
    df = calc_wr(df)
    df = calc_cci(df)
    df = calc_mtm(df)
    df = calc_roc(df)
    df = calc_atr(df)
    df = calc_amplitude(df)
    df = calc_std(df)
    df = calc_volume_ma(df)
    df = calc_amount_ma(df)
    df = calc_volume_ratio(df)
    df = calc_vr(df)
    df = calc_obv(df)
    df = calc_turnover_rate(df)
    df = calc_gap(df)
    df = calc_high_low_open(df)
    df = calc_new_high(df)
    df = calc_new_low(df)
    df = calc_limit_status(df)
    df = calc_box_breakout(df)
    df = calc_vcp_contraction(df)
    df = calc_dmi(df)
    df = calc_bias(df)
    df = calc_ma_slope(df)
    df = calc_stage2_template(df)
    df = calc_breakthrough_pullback(df)
    df = calc_period_returns(df)
    df = calc_three_year_return(df)
    df = calc_drawdown(df)
    df = calc_activity_metrics(df)
    return df

if __name__ == "__main__":
    print("技术指标计算库加载完成。调用 calc_all_indicators(df) 即可一次性计算全部指标。")
